import random
import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
import json
from django.db.models import F, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView, DetailView, CreateView, FormView, UpdateView
from django.views.generic import TemplateView
from redis import Redis

from apps.form import OrderForm, StreamForm, RegisterModelForm, EmailForm, LoginForm, ProfileModelForm, \
    UserPasswordChangeForm, PaymentForm
from apps.models import Category, Product, SiteSettings, Region, District, Payment
from apps.models import User
from root.settings import EMAIL_HOST_USER


def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'apps/profile/sections/search.html', {'products': products, 'query': query})


class HomeListView(ListView):
    queryset = Product.objects.order_by('-created_at')
    template_name = 'apps/product/home.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        category_id = self.request.GET.get('category')
        if category_id:
            context['categories'] = Category.objects.filter(parent_id=category_id)
        else:
            context['categories'] = Category.objects.all()
        return context


class ProductListView(ListView):
    queryset = Product.objects.prefetch_related('images').all()
    template_name = 'apps/product/product-list.html'
    context_object_name = 'products'

    def get_image(self, product):
        image = product.images.first()
        print(image)
        if image:
            return image.image.url
        print(image)
        return '/path/to/default/image.jpg'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.GET.get('category'):
            queryset = queryset.filter(category_id=self.request.GET.get('category'))
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'apps/product/product-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        qs = super().get_context_data(**kwargs)
        qs["regions"] = Region.objects.all()
        return qs


class ContactView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/contacts.html'


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/sections/dashboard.html'


class AdminStreamView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/sections/stream.html'


from django.views.generic import TemplateView
# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse

from apps.models import Order, Stream


class AdminStatisticsView(  TemplateView):

    template_name = 'apps/profile/sections/statistics.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get('search', '')
        streams = Stream.objects.filter(product__isnull=False)

        if search_query:
            streams = streams.filter(
                Q(name__icontains=search_query) |
                Q(product__name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        statistics = []

        total_stats = {
            'name': 'JAMI',
            'total_visits': 0,
            'new': 0,
            'accepted': 0,
            'delivering': 0,
            'delivered': 0,
            'callback': 0,
            'spam': 0,
            'returned': 0,
            'hold': 0,
            'archived': 0,
        }

        for stream in streams:
            if not stream.product:
                continue

            stream_orders = Order.objects.filter(product=stream.product)

            stream_stats = {
                'name': stream.name,
                'total_visits': stream.count,
                'new': stream_orders.filter(status='new').count(),
                'accepted': stream_orders.filter(status='accepted').count(),
                'delivering': stream_orders.filter(status='delivering').count(),
                'delivered': stream_orders.filter(status='delivered').count(),
                'callback': stream_orders.filter(status='callback').count(),
                'spam': stream_orders.filter(status='spam').count(),
                'returned': stream_orders.filter(status='returned').count(),
                'hold': stream_orders.filter(status='hold').count(),
                'archived': stream_orders.filter(status='archived').count(),
            }

            statistics.append(stream_stats)

            for key in total_stats:
                if key != 'name':
                    total_stats[key] += stream_stats[key]

        statistics.append(total_stats)

        context['statistics'] = statistics
        context['search_query'] = search_query

        return context


class AdminPaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/profile/sections/payment.html'

    def get(self, request):
        user = request.user
        form = PaymentForm()

        payments = Payment.objects.filter(user=user).order_by('-date')
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        last_payment_date = payments.first().date if payments.exists() else None

        context = {
            'form': form,
            'payments': payments,
            'total_paid': total_paid,
            'last_payment_date': last_payment_date,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        form = PaymentForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']

            if user.balance < amount:
                messages.error(request, "Balansingizda mablag' yetarli emas.")
                return redirect('payment')  # URL nomi

            payment = form.save(commit=False)
            payment.user = user
            payment.status = False
            payment.save()

            user.balance -= amount
            user.save()

            messages.success(request, "To‘lov so‘rovi yuborildi. Admin tasdiqlashi kerak.")
            return redirect('payment')


        payments = Payment.objects.filter(user=user, status=True).order_by('-date')
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        last_payment_date = payments.first().date if payments.exists() else None

        context = {
            'form': form,
            'payments': payments,
            'total_paid': total_paid,
            'last_payment_date': last_payment_date,
        }
        return render(request, self.template_name, context)

class SendMailFormView(FormView):
    form_class = EmailForm
    template_name = 'apps/auth/register.html'
    success_url = reverse_lazy('check_email')

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        verify_code = random.randrange(10 ** 5, 10 ** 6)
        send_mail(
            subject="Verification Code !!!",
            message=f"{verify_code}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )
        redis = Redis()
        try:
            redis.set(email, verify_code)
            redis.expire(email, time=timedelta(minutes=5))
        finally:
            redis.close()

        return render(self.request, 'apps/auth/check_message.html', {"email": email})

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class RegisterCreateView(CreateView):
    form_class = RegisterModelForm
    template_name = 'apps/auth/register.html'
    success_url = reverse_lazy('home')

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        sms_code = form.cleaned_data.get('sms')
        redis = Redis()
        try:
            redis_code = redis.get(email)
            if not redis_code:
                messages.error(self.request, "Kod muddati tugagan.")
                return redirect('check_email')

            if int(redis_code) != int(sms_code):
                messages.error(self.request, "Kod noto'g'ri !!!")
                return redirect(reverse_lazy('send_email'))

            user = form.save()

            login(self.request, user)

            return redirect(self.success_url)
        finally:
            redis.close()


class ProductDetailDetailView(DetailView):
    model = Product
    template_name = 'apps/product/product-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Order.Region.objects.all()
        return context


class StreamListView(LoginRequiredMixin, ListView):
    template_name = 'apps/profile/sections/stream.html'
    queryset = Stream.objects.all()
    context_object_name = 'streams'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class StreamFormView(FormView):
    form_class = StreamForm
    template_name = 'apps/profile/sections/market.html'

    def form_valid(self, form):
        form.save()
        return redirect('stream')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class StreamDetailView(DetailView):
    queryset = Product.objects.all()
    template_name = 'apps/profile/sections/stream.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['self_stream'] = Stream.objects.filter(product=self.object, owner=self.request.user)
        return context


class StreamOrderView(DetailView, FormView):
    form_class = OrderForm
    queryset = Stream.objects.all()
    template_name = 'apps/product/product-detail.html'
    context_object_name = 'stream'

    def form_valid(self, form):
        if form.is_valid():
            form = form.save(commit=False)
            form.stream = self.get_object()
            form.user = self.request.user
            form.save()
            form.product.price -= self.get_object().discount
            form.deliver_price = SiteSettings.objects.first().deliver_price
        return render(self.request, 'apps/product/product-order.html', {'form': form})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object.product
        product.price -= self.object.discount
        context['product'] = product
        context["regions"] = Region.objects.all()
        stream_id = self.kwargs.get('pk')
        Stream.objects.filter(pk=stream_id).update(count=F('count') + 1)
        return context


class AdminMarketView(LoginRequiredMixin, ListView):
    template_name = 'apps/profile/sections/market.html'
    queryset = Category.objects.all()
    context_object_name = 'categories'

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        products = Product.objects.all()
        if slug := self.request.GET.get("category"):
            products = products.filter(category__slug=slug)
        data['products'] = products
        return data


class OrderCreateView(LoginRequiredMixin, View):
    template_name = 'apps/product/product-detail.html'

    def get(self, request, product_id, **kwargs):
        product = get_object_or_404(Product, id=product_id)
        regions = Region.objects.all()
        return render(request, self.template_name, {'product': product, 'regions': regions})

    def post(self, request, product_id, **kwargs):
        product = get_object_or_404(Product, id=product_id)
        region_id = request.POST.get('region')

        if not region_id:
            context = {
                "messages_error": ["Hudud tanlanmagan. Iltimos, hududni tanlang."],
                "product": product,
                "regions": Region.objects.all()
            }
            return render(request, self.template_name, context=context)

        region = get_object_or_404(Region, id=region_id)
        order = Order(
            name=request.POST.get('name'),
            phone_number=re.sub(r'\D', '', request.POST.get('phone_number')),
            region=region,
            product=product
        )

        try:
            order.clean()
        except ValidationError as e:
            context = {
                "messages_error": [e.message],
                "product": product,
                "regions": Region.objects.all()
            }
            return render(request, self.template_name, context=context)

        order.save()
        return redirect('order_success', order_id=order.id)


class OrderListView(LoginRequiredMixin, ListView):
    template_name = 'apps/product/product-order.html'
    context_object_name = 'operator'

    def get(self, request, order_id, **kwargs):
        order = get_object_or_404(Order, id=order_id)
        products = Product.objects.all()
        return render(request, self.template_name, context={'order': order, 'products': products})

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderedListView(ListView):
    model = Order
    template_name = 'apps/product/product-archived.html'
    context_object_name = 'operator'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['operator'] = self.get_queryset()
        return context


class SettingsUpdateView(LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    fields = 'first_name', 'last_name'
    template_name = 'apps/profile/profile.html'
    success_url = reverse_lazy('settings_page')

    def get_object(self, queryset=None):
        return self.request.user


class LoginFormView(FormView):
    form_class = LoginForm
    template_name = 'apps/auth/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Email yoki parol noto‘g‘ri')
            return redirect('login1')
    def form_invalid(self, form):
        messages.error(self.request, 'Iltimos, barcha maydonlarni to‘g‘ri to‘ldiring')
        return super().form_invalid(form)

class ProfileUpdateView(UpdateView):
    template_name = 'apps/profile/profile.html'
    queryset = User.objects.all()
    success_url = reverse_lazy('home')
    form_class = ProfileModelForm
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["regions"] = Region.objects.all()
        return data

    def form_valid(self, form):
        user = form.save(commit=False)
        user.district = form.cleaned_data.get('district')
        user.address = form.cleaned_data.get('address')
        user.save()

        messages.success(self.request, "Ma'lumotlar muvaffaqiyatli yangilandi.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Iltimos, to'g'ri to'ldiring.")
        return super().form_invalid(form)


def district_list(request):
    region_id = request.GET.get("region_id")
    districts = District.objects.filter(region_id=region_id)
    data = [{"id": i.pk, "name": i.name} for i in districts]
    return JsonResponse(data, safe=False)


class UserPasswordUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserPasswordChangeForm
    template_name = 'apps/profile/chake/check.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, "Parol muvaffaqiyatli yangilandi!")
        return reverse_lazy('password-update')  # Shu view nomini URL'da aniqlang

    def form_valid(self, form):
        user = self.request.user
        old_password = form.cleaned_data.get('old_password')
        new_password = form.cleaned_data.get('new_password')

        if not user.check_password(old_password):
            form.add_error('old_password', 'Eski parol noto‘g‘ri!')
            return self.form_invalid(form)

        user.set_password(new_password)
        user.save()
        # update_session_auth_hash(self.request, user)  # Logout'ni oldini oladi

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Iltimos, barcha maydonlarni to‘g‘ri to‘ldiring.')
        return super().form_invalid(form)


@login_required
@require_GET
def pending_orders_api(request):
    orders = Order.objects.filter(is_confirmed=False).order_by('-created_at')

    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'name': order.name,
            'phone_number': order.phone_number,
            'region': order.region,
            'product_name': order.product.name if order.product else 'Nomaʼlum',
            'product_price': order.product.price if order.product else 0,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
        })

    return JsonResponse(orders_data, safe=False)


@login_required
@require_POST
def confirm_order_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, is_confirmed=False)
        order.is_confirmed = True
        order.status = 'accepted'
        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Buyurtma topilmadi yoki allaqachon tasdiqlangan'})


@login_required
@require_POST
def reject_order_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, is_confirmed=False)
        order.status = 'spam'
        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Buyurtma topilmadi yoki allaqachon tasdiqlangan'})


@login_required
@require_POST
def update_order_status_api(request, order_id):
    try:
        data = json.loads(request.body)
        new_status = data.get('status')

        if new_status not in dict(Order.StatusChoices.choices):
            return JsonResponse({'success': False, 'error': 'Notoʻgʻri status'})

        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Buyurtma topilmadi'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Notoʻgʻri soʻrov formati'})

def operator_orders_view(request):
    return render(request, 'apps/operator/operator.html')