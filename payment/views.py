import braintree
from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order
from shop.recommender import Recommender


def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        # 获得交易token
        nonce = request.POST.get('payment_method_nonce', None)
        # 使用交易token和附加信息，创建并提交交易信息
        result = braintree.Transaction.sale(
            {
                'amount': '{:2f}'.format(order.get_total_cost()),
                'payment_method_nonce': nonce,
                'options': {
                    'submit_for_settlement': True,
                }
            }
        )
        if result.is_success:
            # 标记订单状态为已支付
            order.paid = True
            # 保存交易ID
            order.braintree_id = result.transaction.id
            order.save()
            # 更新Redis中本次购买的商品分数
            r = Recommender()
            order_items = [order_item.product for order_item in order.items.all()]
            r.products_bought(order_items)

            return redirect('payment:done')
        else:
            return redirect('payment:canceled')

    else:
        # 生成临时token交给页面上的JS程序
        client_token = braintree.ClientToken.generate()
        return render(request,
                      'payment/process.html',
                      {'order': order,
                       'client_token': client_token})


def payment_done(request):
    return render(request, 'payment/done.html')


def payment_canceled(request):
    return render(request, 'payment/canceled.html')
