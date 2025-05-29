# import uuid
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager

from django.db import models
from django.db.models import Model, DateTimeField, CharField, SlugField, ImageField, ForeignKey, CASCADE, TextChoices, \
    EmailField, TextField, IntegerField, SET_NULL, FloatField,BooleanField
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class CreatedAtBase(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# class Base(CreatedAtBase):
#     # id = UUIDField(primary_key=True, db_default=RandomUUID(), editable=False) # postgres da ishlatiladi
#     id = UUIDField(default=uuid.uuid4, primary_key=True)  # sqlite uchun basic
#
#     class Meta:
#         abstract = True


class BaseSlugModel(CreatedAtBase):
    name = CharField(max_length=255)
    slug = SlugField(unique=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, **kwargs):
        self.slug = slugify(self.name)
        while self.__class__.objects.filter(slug=self.slug).exists():
            self.slug += '-1'
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name


class CustomerUser(UserManager):
    def _create_user_object(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def _create_user(self, email, password, **extra_fields):
        user = self._create_user_object(email, password, **extra_fields)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = None
    email = EmailField(max_length=255, unique=True)
    address= IntegerField(null=True, blank=True)
    district = ForeignKey('District', on_delete=SET_NULL, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomerUser()
    balance = FloatField(null=True, blank=True)
    status = BooleanField(default=False)


class Category(BaseSlugModel):
    image = ImageField(upload_to='category-image/')


class Product(BaseSlugModel):
    name = CharField(max_length=255)
    price = models.FloatField()
    short_description = CKEditor5Field()
    long_description = CKEditor5Field()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')


class ImageProduct(Model):
    image = ImageField(upload_to='products/%Y/%m/%d/')
    video = models.FileField(upload_to='products/videos/%Y/%m/%d/', blank=True, null=True)
    product = ForeignKey('apps.Product', CASCADE, related_name='images')

    def __str__(self):
        return f"ImageProduct for {self.product}"


from django.db import models
from django.db.models import TextChoices, CharField, ForeignKey, CASCADE

class Order(models.Model):
    class Region(TextChoices):
        ANDIJON = "andijon", "Andijon"
        BUXORO = "buxoro", "Buxoro"
        FARGONA = "fargona", "Farg'ona"
        JIZZAX = "jizzax", "Jizzax"
        XORAZM = "xorazm", "Xorazm"
        NAMANGAN = "namangan", "Namangan"
        NAVOIY = "navoiy", "Navoiy"
        QASHQADARYO = "qashqadaryo", "Qashqadaryo"
        QORAQALPOGISTON = "qoraqalpogiston", "Qoraqalpog'iston"
        SAMARQAND = "samarqand", "Samarqand"
        SIRDARYO = "sirdaryo", "Sirdaryo"
        SURXONDARYO = "surxondaryo", "Surxondaryo"
        TOSHKENT = "toshkent", "Toshkent"

    class StatusChoices(TextChoices):
        NEW = 'new', 'Yangi'
        ACCEPTED = 'accepted', 'Qabul qilindi'
        DELIVERING = 'delivering', 'Yetkazilmoqda'
        DELIVERED = 'delivered', 'Yetkazildi'
        CALLBACK = 'callback', 'Qayta aloqa'
        SPAM = 'spam', 'Spam'
        RETURNED = 'returned', 'Qaytarilgan'
        HOLD = 'hold', 'Kutilmoqda'
        ARCHIVED = 'archived', 'Arxivlangan'

    name = CharField(max_length=50)
    phone_number = CharField(max_length=50)
    region = CharField(max_length=255, choices=Region.choices)
    product = ForeignKey('apps.Product', CASCADE, to_field='slug', related_name='operator')
    status = CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_confirmed = models.BooleanField(default=False)


class Review(Model):
    name = CharField(max_length=255)
    email = EmailField(max_length=255, null=True, blank=True)
    description = TextField()
    comment_status = TextField()
    created_at = DateTimeField(auto_now_add=True)
    product = ForeignKey('apps.Product', CASCADE, related_name='reviw')

    def __str__(self):
        return self.name


class Region(Model):
    name = CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class District(Model):
    name = CharField(max_length=255, unique=True)
    region = ForeignKey('apps.Region', CASCADE, related_name='districts')

    def __str__(self):
        return self.name


class Stream(CreatedAtBase):
    name = CharField(max_length=255)
    discount = FloatField()
    count = IntegerField(default=0)
    product = ForeignKey('apps.Product', SET_NULL, null=True, related_name='streams')
    user = ForeignKey('apps.User', CASCADE, related_name='streams')

    class Meta:
        ordering = '-id',

    def str(self):
        return self.name


class SiteSettings(Model):
    pass

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)  # False - kutilmoqda, True - to‘langan

    def __str__(self):
        return f"{self.user.username} - {self.amount} so'm"





