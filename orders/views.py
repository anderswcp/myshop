from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .task import order_created
from django.urls import reverse


def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'],
                                         quantity=item['quantity'])
            # 成功生成OrderItem之后清除购物车
            cart.clear()
            # 清除优惠券信息
            request.session['coupon_id'] = None
            order_created.delay(order.id)
            # return render(request, 'order/created.html', {'order': order})
            # 在session中加入订单id
            request.session['order_id'] = order.id
            # 重定向到支付页面
            return redirect(reverse('payment:process'))

    else:
        form = OrderCreateForm()
    return render(request, 'order/create.html', {'cart': cart, 'form': form})
