from unittest import mock, TestCase, skip
from unittest.mock import patch

from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete
from django.db.models.signals import post_delete
from model_bakery import baker

from apps.soft_delete.exceptions import SoftDeleteException
from apps.soft_delete.signals import post_soft_delete
from apps.soft_delete.signals import post_hard_delete
from apps.soft_delete.signals import post_restore

from django.utils import timezone
from apps.expert_shop.models import *
from base_utils.base_tests import TainoBaseServiceTestCase


@skip("for later")
class TestSoftDeleteModel(TainoBaseServiceTestCase):
    """

    The TestSoftDeleteModel class contains test methods for testing the functionality
    of soft deletion and restoration of objects.

    """

    def assert_objects_count(self, model, a: int, d: int, g: int = None):
        """
        Assert Objects Count Method

        This method is used to assert the count of objects, deleted objects, and global objects in a given model.

        :param model: The model for which the counts are to be asserted.
        :type model: Any valid Django model.
        :param a: The expected count of objects in the model.
        :type a: int
        :param d: The expected count of deleted objects in the model.
        :type d: int
        :param g: The expected count of global objects in the model. Default is None, which will be calculated as the sum of `a` and `d`.
        :type g: int, optional
        :return: A boolean value indicating whether the counts match the expected values. Returns True if all counts match, False otherwise.
        :rtype: bool

        Example usage:
            >>> assert_objects_count(MyModel, 10, 5)
            True
            >>> assert_objects_count(MyModel, 10, 5, 15)
            True
            >>> assert_objects_count(MyModel, 10, 5, 14)
            False
        """
        if g is None:
            g = a + d
        return all(
            [
                model.objects.count() == a,
                model.deleted_objects.count() == d,
                model.global_objects.count() == g,
            ]
        )

    def assert_object_in(self, obj, a: bool, d: bool, g: bool = None):
        """
        Asserts that the given object exists in the specified model or models.

        :param obj: The object to assert existence for.
        :param a: A boolean indicating whether the object should exist in the model's regular objects.
        :param d: A boolean indicating whether the object should exist in the model's deleted_objects.
        :param g: A boolean indicating whether the object should exist in the model's global_objects (optional).
        :return: True if the object exists in all specified models, False otherwise.
        """
        model = obj.__class__
        s = [
            model.objects.filter(id=obj.id).exists() is a,
            model.deleted_objects.filter(id=obj.id).exists() is d,
        ]
        if g is not None:
            s.append(model.global_objects.filter(id=obj.id).exists() is g)
        return all(s)

    def test_is_deleted(self):
        """
        Check if the 'is_deleted' attribute of a product is set correctly.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True, _fill_optional=True)

        now = timezone.now()
        assert not product.is_deleted
        assert product.deleted_at is None
        product.deleted_at = now
        product.save()
        assert product.is_deleted

    def test_is_restored(self):
        """
        Check if the 'is_deleted' attribute of a product is set correctly.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True)
        now = timezone.now()
        assert not product.is_restored
        assert product.restored_at is None
        product.restored_at = now
        product.save()
        assert product.is_restored

    def test_soft_delete(self):
        """
        Test the soft delete functionality of a product.
        """

        product = baker.make(ExpertShopProduct, make_m2m=True, country=None, city=None)
        assert not product.is_deleted
        assert self.assert_objects_count(ExpertShopProduct, 1, 0, 1)

        product.delete()
        product.refresh_from_db()
        assert product.is_deleted
        assert self.assert_objects_count(ExpertShopProduct, 0, 1, 1)

    # def test_soft_deleted_objects_keep_relations(
    #         self, product_factory, option, product_landing, product,
    # ):
    #     # product = product_factory(option=option, landing=product_landing)
    #     shop = product.shop
    #     print(shop.product_set.all())
    #     product.delete()
    #
    #     # assert Option.deleted_objects.filter(product__pk=product.pk).exists()
    #     # assert ProductLanding.deleted_objects.filter(product__pk=product.pk).exists()
    #     # assert Shop.deleted_objects.filter(pk=product.shop.pk).exists()
    #     # shop.refresh_from_db()
    #     print(product.pk)
    #     print(shop.product_set.all())
    #     print(shop.product_set.filter(pk=product.pk))
    #     assert shop.product_set.filter(pk=product.pk).exists()

    def test_hard_delete(self):
        """
        Delete the product permanently from the database.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True)
        obj_id = product.id
        product.hard_delete()

        with self.assertRaises(ExpertShopProduct.DoesNotExist):
            ExpertShopProduct.objects.get(id=obj_id)

        assert self.assert_objects_count(ExpertShopProduct, 0, 0, 0)

    def test_restore(self):
        """
        Restores a deleted product in the database.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True)
        product.delete()
        obj_id = product.id

        product.restore()
        product.refresh_from_db()
        assert not product.is_deleted
        assert product.id == obj_id
        assert product.is_restored

        assert self.assert_objects_count(ExpertShopProduct, 1, 0, 1)

    def test_queryset_soft_delete(self):
        """
        Test soft deleting queryset.
        """
        obj1 = baker.make(ExpertShopProduct, make_m2m=True)
        obj2 = baker.make(ExpertShopProduct, make_m2m=True)
        obj3 = baker.make(ExpertShopProduct, make_m2m=True)

        ExpertShopProduct.objects.filter(id=obj1.id).delete()
        assert self.assert_objects_count(ExpertShopProduct, 2, 1, 3)
        assert self.assert_object_in(obj1, False, True, True)

        obj1.refresh_from_db()
        assert obj1.is_deleted

    def test_queryset_soft_delete_multiple(self):
        """
        Test the soft deletion of multiple objects in the queryset.
        """
        obj1 = baker.make(ExpertShopProduct, make_m2m=True)
        obj2 = baker.make(ExpertShopProduct, make_m2m=True)
        obj3 = baker.make(ExpertShopProduct, make_m2m=True)

        ids = [
            obj1.id,
            obj2.id,
        ]
        ExpertShopProduct.objects.filter(id__in=ids).delete()
        assert self.assert_objects_count(ExpertShopProduct, 1, 2, 3)
        assert self.assert_object_in(obj1, False, True, True)
        assert self.assert_object_in(obj2, False, True, True)
        assert self.assert_object_in(obj3, True, False, True)

        obj1.refresh_from_db()
        assert obj1.is_deleted
        obj2.refresh_from_db()
        assert obj2.is_deleted
        obj3.refresh_from_db()
        assert not obj3.is_deleted

    def test_queryset_hard_delete(self):
        """
        Test the hard delete functionality of the queryset.
        """
        obj1 = baker.make(ExpertShopProduct, make_m2m=True)
        obj2 = baker.make(ExpertShopProduct, make_m2m=True)
        obj3 = baker.make(ExpertShopProduct, make_m2m=True)

        ids = [
            obj1.id,
            obj2.id,
        ]
        ExpertShopProduct.objects.filter(id__in=ids).hard_delete()
        assert self.assert_objects_count(ExpertShopProduct, 1, 0, 1)
        assert self.assert_object_in(obj1, False, False, False)
        assert self.assert_object_in(obj2, False, False, False)
        assert self.assert_object_in(obj3, True, False, True)

        with self.assertRaises(ExpertShopProduct.DoesNotExist):
            ExpertShopProduct.objects.get(id=obj1.id)
        with self.assertRaises(ExpertShopProduct.DoesNotExist):
            ExpertShopProduct.objects.get(id=obj2.id)
        assert ExpertShopProduct.objects.filter(id=obj3.id).exists()

    def test_queryset_restore(self):
        """
        Test the restoration of deleted objects in the queryset.
        """
        obj1 = baker.make(ExpertShopProduct, make_m2m=True)
        obj2 = baker.make(ExpertShopProduct, make_m2m=True)
        obj3 = baker.make(ExpertShopProduct, make_m2m=True)

        ids = [
            obj1.id,
            obj2.id,
        ]

        ExpertShopProduct.objects.all().delete()
        ExpertShopProduct.deleted_objects.filter(id__in=ids).restore()
        assert self.assert_objects_count(ExpertShopProduct, 2, 1, 3)
        assert self.assert_object_in(obj1, True, False, True)
        assert self.assert_object_in(obj2, True, False, True)
        assert self.assert_object_in(obj3, False, True, True)

        obj1.refresh_from_db()
        assert not obj1.is_deleted
        assert obj1.is_restored
        obj2.refresh_from_db()
        assert not obj2.is_deleted
        assert obj2.is_restored
        obj3.refresh_from_db()
        assert obj3.is_deleted
        assert not obj3.is_restored

    def test_delete_cascade(self):
        """
        The test_delete_cascade method is responsible for testing the cascade
        delete functionality of a product.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True)
        product.delete()

        comment = baker.make(ExpertShopProductComments)

        comment.refresh_from_db()
        assert self.assert_object_in(comment, False, True, True)
        assert comment.is_deleted

        # The model the product related to is still alive
        assert self.assert_object_in(product, True, False, True)
        assert not product.is_deleted

    def test_restore_cascade(self):
        """
        The test is responsible for testing the cascade
        restoring functionality of a product.
        """
        comment = baker.make(ExpertShopProductComments)
        product = comment.product
        product.delete()

        # Test restore
        product.restore()

        # product = ExpertShopProduct.global_objects.get(pk=product.pk)
        # comment = ExpertShopProductComments.global_objects.get(pk=option.pk)

        product.refresh_from_db()
        comment.refresh_from_db()
        assert self.assert_object_in(product, True, False, True)
        assert self.assert_object_in(comment, True, False, True)
        assert not product.is_deleted
        assert not comment.is_deleted

        assert product.is_restored
        assert comment.is_restored

    def test_restore_cascade_only_within_transaction(self):
        """
        The test is responsible for testing the cascade
        restoring functionality of a related object.
        """
        shop_category = baker.make(ShopCategory)
        bread = baker.make(ExpertShopProduct, make_m2m=True, name="Bread")
        bread.shop_category = shop_category
        bread.save()
        chips = baker.make(ExpertShopProduct, make_m2m=True, name="Chips")
        chips.shop_category = shop_category
        chips.save()
        chips.delete()  # Deleted before shop, in another transaction
        shop_category.delete()

        # Test restore
        shop_category.restore()

        chips.refresh_from_db()
        bread.refresh_from_db()
        shop_category.refresh_from_db()
        assert self.assert_object_in(chips, False, True, True)
        assert self.assert_object_in(bread, True, False, True)
        assert self.assert_object_in(shop_category, True, False, True)
        assert chips.is_deleted
        assert not bread.is_deleted
        assert not shop_category.is_deleted
        assert not chips.is_restored
        assert bread.is_restored
        assert shop_category.is_restored
        assert chips.sid is not None
        assert bread.sid is None
        assert shop_category.sid is None

    def test_hard_delete_cascade(self):
        """
        Test the hard delete cascade functionality.
        """
        comment = baker.make(ExpertShopProductComments)
        product = comment.product
        product.hard_delete()
        assert not ExpertShopProduct.deleted_objects.filter(id=product.id)
        assert not ExpertShopProductComments.objects.filter(id=comment.id).exists()

    def test_delete_reverse_cascade(self):

        category = baker.make(ShopCategory)
        product = baker.make(ExpertShopProduct, make_m2m=True, category=category)
        category.delete()
        product.refresh_from_db()
        assert product.is_deleted

    def test_atomic(self):
        """
        This test checks if deletion and restore methods of the SoftDeleteModel
        are atomic and can roll back in case of an error.
        """
        product = baker.make(ExpertShopProduct, make_m2m=True)
        with patch("apps.expert_shop.models.ExpertShopProduct.save") as mock_save:
            mock_save.side_effect = ValueError("Artificial error")
            with self.assertRaises(ValueError) as e:
                product.delete()
            assert str(e.value) == "Artificial error"
        assert self.assert_object_in(product, True, False, True)

    # @mock.patch("apps.expert_shop")
    # def test_signal_calls_on_soft_delete(self):
    #     with (
    #         signal_mock(pre_delete, ExpertShopProduct) as pre_delete_mock,
    #         signal_mock(post_delete, ExpertShopProduct) as post_delete_mock,
    #         signal_mock(post_soft_delete, ExpertShopProduct) as post_soft_delete_mock,
    #     ):
    #         product = baker.make(ExpertShopProduct, make_m2m=True)
    #         product.delete()
    #         assert pre_delete_mock.call_count == 1
    #         assert post_delete_mock.call_count == 1
    #         assert post_soft_delete_mock.call_count == 1

    # def test_signal_calls_on_hard_delete(self):
    #     with (
    #         signal_mock(pre_delete, ExpertShopProduct) as pre_delete_mock,
    #         signal_mock(post_delete, ExpertShopProduct) as post_delete_mock,
    #         signal_mock(post_hard_delete, ExpertShopProduct) as post_hard_delete_mock,
    #     ):
    #         product = baker.make(ExpertShopProduct, make_m2m=True)
    #         product.hard_delete()
    #         assert pre_delete_mock.call_count == 1
    #         assert post_delete_mock.call_count == 1
    #         assert post_hard_delete_mock.call_count == 1

    # def test_signal_calls_on_restore(self):
    #     with signal_mock(post_restore, ExpertShopProduct) as post_restore_mock:
    #         product = baker.make(ExpertShopProduct, make_m2m=True)
    #         product.restore()
    #         assert post_restore_mock.call_count == 1

    def test_delete_with_restricted_relation(self, product_restricted_category, category):
        p = product_restricted_category
        with self.assertRaises(ProtectedError) as e:
            category.delete()
            err_msg = str(e.value)
            assert f"Cannot delete Category object ({category.pk})" in err_msg
            assert f"ProductRestrictedCategory object ({p.pk})" in err_msg
            assert f"related with RESTRICT" in err_msg

        p.refresh_from_db()
        assert not p.is_deleted
        assert not category.is_deleted

    # def test_delete_with_not_soft_delete_model_relation(
    #         self, not_soft_related_model, product_not_soft_relation,
    # ):
    #     with self.assertRaises(SoftDeleteException) as e:
    #         product_not_soft_relation.delete()
    #     assert str(e.value) == "NotSoftRelatedModel is not a subclass of SoftDeleteModel."

    def test_delete_only_target_instances(self):
        product = baker.make(ExpertShopProduct, make_m2m=True)
        another_product = baker.make(ExpertShopProduct, make_m2m=True)
        comment = baker.make(ExpertShopProductComments)
        another_comment = baker.make(ExpertShopProductComments)
        product.delete()
        product.refresh_from_db()
        comment.refresh_from_db()
        another_product.refresh_from_db()
        another_comment.refresh_from_db()
        assert product.is_deleted
        assert comment.is_deleted
        assert not another_product.is_deleted
        assert not another_comment.is_deleted
