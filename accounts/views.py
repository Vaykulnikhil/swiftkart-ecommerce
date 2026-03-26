from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile
from orders.models import Order   
from django.contrib import messages,auth
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


#vefification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
from carts.views import cart_id
from carts.models import Cart,CartItem
import requests
from orders.models import OrderProduct


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            if Account.objects.filter(email=email).exists():
                messages.error(request, 'Account with this Email already exists.')
                return redirect('register')

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=email,
                password=password
            )
            user.phone_number = phone_number
            user.save()

            #Create user profile
            profile=UserProfile()
            profile.user_id=user.id
            profile.profile_picture='default/default-user.png'
            profile.save()

            #user Activation
            current_site=get_current_site(request)
            mail_subject='please activate your account'
            message=render_to_string('accounts/account_verification_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=[email]
            send_email=EmailMessage(mail_subject,message,settings.EMAIL_HOST_USER,to_email)
            send_email.send(fail_silently=False)
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your email address[swiftkart@zohomail.in].please verify it.')
            return redirect(f'/accounts/login/?command=verification&email={user.email}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, 'Invalid login credentials')
            return redirect('accounts:login')

        try:
            cart = Cart.objects.get(cart_id=cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)

            if cart_items.exists():

                # variations from session cart
                product_variation = []
                for item in cart_items:
                    product_variation.append(list(item.variations.all()))

                # variations from user cart
                cart_items_user = CartItem.objects.filter(user=user)
                ex_var_list = []
                ids = []

                for item in cart_items_user:
                    ex_var_list.append(list(item.variations.all()))
                    ids.append(item.id)

                # compare and merge
                for pr in product_variation:
                    if pr in ex_var_list:
                        index = ex_var_list.index(pr)
                        item_id = ids[index]
                        item = CartItem.objects.get(id=item_id)
                        item.quantity += 1
                        item.save()
                    else:
                        cart_items = CartItem.objects.filter(cart=cart)
                        for item in cart_items:
                            item.user = user
                            item.save()

        except Cart.DoesNotExist:
            pass

        #  LOGIN MUST ALWAYS HAPPEN
        auth_login(request, user)
        messages.success(request, 'You are now logged in.')
        url=request.META.get('HTTP_REFERER')
        try:
            query=requests.utils.urlparse(url).query
            print('query ->',query)
            
            #next=/cart/checkout/
            params=dict(x.split('=')for x in query.split('&'))
            if 'next' in params:
                nextPage=params['next']
                return redirect(nextPage)
        except:
            pass
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)

        return redirect('accounts:dashboard')

    # GET REQUEST
    return render(request, 'accounts/login.html')


@login_required(login_url='accounts:login')
def logout(request):
    auth.logout(request)
    messages.success(request,'you are logged out.')
    return redirect('accounts:login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request,'invalid activation link')
        return redirect('register')

@login_required(login_url='accounts:login')
def dashboard(request):
    orders=Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
    orders_count=orders.count()

    userprofile=UserProfile.objects.get(user_id=request.user.id)

    context={
        'orders_count':orders_count,
        'userprofile':userprofile,
    }
    return render(request,'accounts/dashboard.html',context)


def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST['email']

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset your Password'

            email_body = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            send_email = EmailMessage(
                mail_subject,
                email_body,
                settings.EMAIL_HOST_USER,
                [email],
            )
            send_email.send(fail_silently=False)

            messages.success(
                request,
                'Password reset email has been sent to your email address.'
            )
            return redirect('login')

        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid']=uid
        messages.success(request,'please reset your password ')
        return redirect('resetPassword')
    else:
        messages.error(request,'This link has been expired')
        return redirect('login')
    


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password and confirm_password and password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match')
            return redirect('resetPassword')

    return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    orders=Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context={
        'orders':orders,
    }
    return render(request, 'accounts/my_orders.html',context)

@login_required(login_url='login')
def edit_profile(request):
    userprofile=get_object_or_404(UserProfile,user=request.user)
    if request.method=='POST':
        user_form=UserForm(request.POST,instance=request.user)
        profile_form=UserProfileForm(request.POST,request.FILES,instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,'Your profile has been updated')
            return redirect('accounts:edit_profile')
    else:
        user_form=UserForm(instance=request.user)
        profile_form=UserProfileForm(instance=userprofile)
    context={
        'user_form':user_form,
        'profile_form':profile_form,
        'userprofile':userprofile,
    }
    return render(request, 'accounts/edit_profile.html',context)

@login_required(login_url='login')
def change_password(request):
    if request.method=='POST':
        current_password=request.POST['current_password']
        new_password=request.POST['new_password']
        confirm_password=request.POST['confirm_password']

        user=Account.objects.get(username__exact=request.user.username)

        if new_password==confirm_password:
            success=user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                #auth.logout(request)
                messages.success(request, 'Password updated sucessfully')
                return redirect('accounts:change_password')
            else:
                messages.error(request,'Please enter valid current password')
                return redirect('accounts:change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('accounts:change_password')
    return render(request,'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_detail = OrderProduct.objects.filter(order=order)
    subtotal=0
    for i in  order_detail:
              subtotal +=i.product_price * i.quantity

    context = {
        'order': order,
        'order_detail': order_detail,
        'subtotal':subtotal,
        
    }
    return render(request, 'accounts/order_detail.html', context)
