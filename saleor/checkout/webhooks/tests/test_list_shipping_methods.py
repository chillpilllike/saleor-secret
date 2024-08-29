import json
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import graphene
from django.utils import timezone

from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_checkout_payload
from ....webhook.transport.asynchronous import create_deliveries_for_subscriptions
from ....webhook.transport.shipping import (
    get_cache_data_for_shipping_list_methods_for_checkout,
)
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ..list_shipping_methods import (
    CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    ShippingListMethodsForCheckout,
)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_webhook_response_none(
    mocked_webhook,
    checkout_ready_to_complete,
    shipping_app,
):
    # given
    checkout = checkout_ready_to_complete
    mocked_webhook.return_value = None

    # when
    methods = ShippingListMethodsForCheckout.list_shipping_methods(checkout)

    # then
    assert not methods


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_set_cache(
    mocked_webhook,
    mocked_cache_set,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook.return_value = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]

    # when
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert mocked_webhook.called
    assert mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_no_webhook_response_does_not_set_cache(
    mocked_webhook,
    mocked_cache_set,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook.return_value = None

    # when
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert mocked_webhook.called
    assert not mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_use_cache(
    mocked_webhook,
    mocked_cache_get,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_cache_get.return_value = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]

    # when
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert not mocked_webhook.called
    assert mocked_cache_get.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_use_cache_for_empty_list(
    mocked_webhook,
    mocked_cache_get,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_cache_get.return_value = []

    # when
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert not mocked_webhook.called
    assert mocked_cache_get.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_change_invalidates_cache_key(
    mocked_webhook,
    mocked_cache_get,
    mocked_cache_set,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook_response = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    mocked_webhook.return_value = mocked_webhook_response
    mocked_cache_get.return_value = None

    payload = generate_checkout_payload(checkout_with_item)
    key_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )

    # when
    checkout_with_item.email = "newemail@example.com"
    checkout_with_item.save(update_fields=["email"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert cache_key != new_cache_key
    mocked_cache_get.assert_called_once_with(new_cache_key)
    mocked_cache_set.assert_called_once_with(
        new_cache_key,
        mocked_webhook_response,
        timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_ignore_selected_fields_on_generating_cache_key(
    mocked_webhook,
    mocked_cache_get,
    mocked_cache_set,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook_response = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    mocked_webhook.return_value = mocked_webhook_response
    mocked_cache_get.return_value = None

    payload = generate_checkout_payload(checkout_with_item)
    key_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )

    # when
    checkout_with_item.last_change = timezone.now() + timedelta(seconds=30)
    checkout_with_item.save(update_fields=["last_change"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    ShippingListMethodsForCheckout.list_shipping_methods(checkout_with_item)

    # then
    assert cache_key == new_cache_key
    mocked_cache_get.assert_called_once_with(new_cache_key)
    mocked_cache_set.assert_called_once_with(
        new_cache_key,
        mocked_webhook_response,
        timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


def test_shipping_list_methods_for_checkout(
    checkout_with_shipping_required,
    subscription_webhook,
    address,
    shipping_method,
):
    # given
    query = """
    subscription {
      event {
        ...on ShippingListMethodsForCheckout {
          checkout {
            id
          }
        }
      }
    }
    """
    event_type = ShippingListMethodsForCheckout.event_type
    webhook = subscription_webhook(query, event_type)
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [webhook]
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload["checkout"] == {"id": checkout_id}
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
