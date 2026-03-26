from django.shortcuts import render, redirect
from django.http import HttpResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order,Payment,OrderProduct
from django.utils import timezone
import razorpay
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string




def payments(request):
    if request.method == "POST":
        body = json.loads(request.body)

        order_number = body.get('orderID')

        if not order_number:
            return JsonResponse({"status": "error", "message": "Order ID not received"})

        try:
            order = Order.objects.get(order_number=order_number, is_ordered=False)
        except Order.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Order not found"})

        #  Create Payment
        payment = Payment.objects.create(
            user=order.user,
            payment_id=body.get("razorpay_payment_id"),
            payment_method="Razorpay",
            amount_paid=order.order_total,
            status="Completed",
        )

        # Update Order
        order.payment = payment
        order.is_ordered = True
        order.status = "Completed"
        order.save()

        # 3 Move Cart Items to OrderProduct
        cart_items = CartItem.objects.filter(user=order.user)

        for item in cart_items:
            orderproduct = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=order.user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                ordered=True
            )

            orderproduct.variations.set(item.variations.all())

            # Reduce stock
            product = item.product
            product.stock -= item.quantity
            product.save()

        cart_items.delete()

        # SEND EMAIL (MOST IMPORTANT PART)
        try:
            mail_subject = "Thank you for your order"

            message = render_to_string(
                "orders/order_received_email.html",
                {
                    "user": order.user,
                    "order": order,
                }
            )

            email = EmailMessage(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [order.user.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)

            #send order number and transaction id back to sendData method via JasonResponse
            data={
                'order_number':order.order_number,
                'transID':payment.payment_id,
            }
            return JsonResponse(data)
            print("EMAIL SENT SUCCESSFULLY")

        except Exception as e:
            print("EMAIL ERROR:", e)

        return JsonResponse({
            "status": "success",
            "order_number": order.order_number,
            "payment_id": payment.payment_id
        })


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # if the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            # store all the billing information inside order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')

            # SAVE ORDER
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = timezone.now()
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            
            order=Order.objects.get(user=current_user,is_ordered=False, order_number=order_number)
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total,
                 'razorpay_key': settings.RAZORPAY_KEY_ID,
            }
            return render(request,'orders/payments.html',context)

        else:
            return redirect('carts:checkout')



def create_order(request):

    if request.method == "POST":
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        order = Order.objects.filter(
            user=request.user,
            is_ordered=False
        ).last()

        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        amount = int(order.order_total * 100)

        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        #  IMPORTANT – Save razorpay order id
        order.razorpay_order_id = razorpay_order["id"]
        order.save()

        return JsonResponse({
            "order_id": razorpay_order["id"],
            "amount": amount,
            "order_number": order.order_number   
        })

    return JsonResponse({"error": "Invalid request"}, status=400)


def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)

        payment = Payment.objects.get(payment_id=payment_id)

        subtotal = 0
        for item in ordered_products:
            subtotal += item.product_price * item.quantity

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'subtotal': subtotal,
            'tax': order.tax,
            'grand_total': order.order_total,
            'payment': payment,
            'transID': payment.payment_id,
        }

        return render(request, "orders/order_complete.html", context)

    except Exception as e:
        return redirect('home')
