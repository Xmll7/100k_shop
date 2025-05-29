from django.contrib.auth.views import LogoutView
from django.urls import path

from apps import views
from apps.views import HomeListView, ProductListView, ProductDetailView, AdminDashboardView, \
    AdminMarketView, AdminStatisticsView, StreamListView, AdminPaymentView, OrderCreateView, \
    StreamFormView, OrderListView, OrderedListView, StreamOrderView, search_products, SendMailFormView, \
    RegisterCreateView, LoginFormView, ProfileUpdateView,  UserPasswordUpdateView

urlpatterns = [
    path('', HomeListView.as_view(), name='home'),
    path('product/', ProductListView.as_view(), name='product-list-page'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product-detail-page'),
    path('contacts', AdminDashboardView.as_view(), name='contacts'),
    path('login/', RegisterCreateView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('admin1/', AdminDashboardView.as_view(), name='dashboard'),
    path('admin1/market', AdminMarketView.as_view(), name='market'),
    path('admin1/statistics', AdminStatisticsView.as_view(), name='statistics'),
    path('admin1/payment', AdminPaymentView.as_view(), name='payment'),
    path('admin1/stream-form', StreamFormView.as_view(), name='stream-form'),
    path('admin1/list-stream', StreamListView.as_view(), name='stream'),
    path('oqim/<int:pk>', StreamOrderView.as_view(), name='Stream'),

    path('order-create/<int:product_id>/', OrderCreateView.as_view(), name='product-order'),

    path('order/success/<int:order_id>/', OrderListView.as_view(), name='order_success'),
    path('operator/', OrderListView.as_view(), name='order_list'),
    path('product/archived', OrderedListView.as_view(), name='product-archived'),
    path('search/', search_products, name='search_products'),
    path('send-email', SendMailFormView.as_view(), name='send_email'),
    path('check-email', RegisterCreateView.as_view(), name='check_email'),
    path('register/', RegisterCreateView.as_view(), name='register'),
    path('logn/', LoginFormView.as_view(), name='login1'),
    path('profile/<int:pk>', ProfileUpdateView.as_view(), name='profile-update-page'),
    path('user_profile/<int:pk>/', ProfileUpdateView.as_view(), name='profile'),
    path('check-profile', RegisterCreateView.as_view(), name='check-profile'),
    path('districts/', views.district_list, name='district_list'),
    path('password/', UserPasswordUpdateView.as_view(), name='password-update'),

    path('operator/orders/', views.operator_orders_view, name='operator_orders'),
    path('api/orders/pending/', views.pending_orders_api, name='pending_orders_api'),
    path('api/orders/<int:order_id>/confirm/', views.confirm_order_api, name='confirm_order_api'),
    path('api/orders/<int:order_id>/reject/', views.reject_order_api, name='reject_order_api'),
    path('api/orders/<int:order_id>/update_status/', views.update_order_status_api, name='update_order_status_api'),
]
