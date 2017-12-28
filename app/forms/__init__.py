# -*- coding: utf-8 -*-

from .user_forms import RoleForm, AbilityForm, SiteForm, UserForm, PasswdForm, PreferenceForm
from .setting_forms import StoreForm, CurrencyForm, ClientForm
from .warehouse_forms import WarehouseForm
from .product_forms import ProductForm, SupplierForm, CategoryForm, EditCategoryForm, ProductSkuForm, BrandForm, ProductGroupForm
from .purchase_forms import PurchaseForm, PurchaseExpressForm
from .order_forms import OrderForm, OrderExpressForm, OrderRemark
from .logistics_forms import ExpressForm, EditExpressForm, ShipperForm
from .application_forms import ApplicationForm
from .customer_forms import CustomerForm, CustomerGradeForm, CustomerEditForm, DiscountTempletForm, DiscountTempletEditForm
from .h5mall_forms import H5mallForm
from .address_forms import PlaceForm, CountryForm, EditCountryForm