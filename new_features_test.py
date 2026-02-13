#!/usr/bin/env python3
"""
اختبار شامل للميزات الجديدة المطلوبة من المستخدم:
1. تحديث أسماء طرق الدفع
2. نظام تغيير طرق الدفع في الفواتير  
3. نظام إلغاء الفواتير
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class NewFeaturesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.created_resources = {
            'customers': [],
            'invoices': [],
            'raw_materials': [],
            'inventory_items': []
        }
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ نجح" if success else "❌ فشل"
        print(f"{status} - {test_name}")
        if details:
            print(f"   التفاصيل: {details}")
        if error:
            print(f"   الخطأ: {error}")
        print()

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    def setup_test_data(self):
        """إعداد البيانات الأساسية للاختبار"""
        print("🔧 إعداد البيانات الأساسية للاختبار...")
        
        # إنشاء عميل للاختبار
        customer_data = {
            "name": "عميل اختبار الميزات الجديدة",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        response = self.make_request('POST', '/customers', customer_data)
        if response and response.status_code == 200:
            customer = response.json()
            self.created_resources['customers'].append(customer['id'])
            self.test_customer_id = customer['id']
            print(f"✅ تم إنشاء عميل الاختبار: {customer['name']}")
        else:
            print("❌ فشل في إنشاء عميل الاختبار")
            return False
            
        # إنشاء عناصر جرد للاختبار
        inventory_items = [
            {"material_type": "NBR", "inner_diameter": 20.0, "outer_diameter": 30.0, "available_pieces": 100},
            {"material_type": "BUR", "inner_diameter": 25.0, "outer_diameter": 35.0, "available_pieces": 50}
        ]
        
        for item_data in inventory_items:
            response = self.make_request('POST', '/inventory', item_data)
            if response and response.status_code == 200:
                item = response.json()
                self.created_resources['inventory_items'].append(item['id'])
                print(f"✅ تم إنشاء عنصر جرد: {item_data['material_type']} {item_data['inner_diameter']}×{item_data['outer_diameter']}")
        
        # إنشاء مواد خام للاختبار
        raw_materials = [
            {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 30.0,
                "height": 100.0,
                "pieces_count": 10,
                "cost_per_mm": 1.5
            },
            {
                "material_type": "BUR", 
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 80.0,
                "pieces_count": 8,
                "cost_per_mm": 2.0
            }
        ]
        
        for material_data in raw_materials:
            response = self.make_request('POST', '/raw-materials', material_data)
            if response and response.status_code == 200:
                material = response.json()
                self.created_resources['raw_materials'].append(material['id'])
                print(f"✅ تم إنشاء مادة خام: {material_data['material_type']} {material_data['inner_diameter']}×{material_data['outer_diameter']}")
        
        return True

    def test_payment_method_names_update(self):
        """اختبار تحديث أسماء طرق الدفع"""
        print("🧪 اختبار 1: تحديث أسماء طرق الدفع")
        
        # اختبار إنشاء فاتورة بطريقة الدفع الجديدة "فودافون 010"
        invoice_data = {
            "customer_name": "عميل اختبار فودافون 010",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 8.0,
                    "quantity": 5,
                    "unit_price": 10.0,
                    "total_price": 50.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "فودافون 010"
        }
        
        response = self.make_request('POST', '/invoices', invoice_data)
        if response and response.status_code == 200:
            invoice = response.json()
            self.created_resources['invoices'].append(invoice['id'])
            
            if invoice['payment_method'] == "فودافون 010":
                self.log_result(
                    "إنشاء فاتورة بطريقة دفع فودافون 010",
                    True,
                    f"تم إنشاء الفاتورة {invoice['invoice_number']} بطريقة الدفع الجديدة"
                )
            else:
                self.log_result(
                    "إنشاء فاتورة بطريقة دفع فودافون 010",
                    False,
                    f"طريقة الدفع المحفوظة: {invoice['payment_method']}"
                )
        else:
            self.log_result(
                "إنشاء فاتورة بطريقة دفع فودافون 010",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # اختبار إنشاء فاتورة بطريقة الدفع الجديدة "كاش 0100"
        invoice_data['payment_method'] = "كاش 0100"
        invoice_data['customer_name'] = "عميل اختبار كاش 0100"
        
        response = self.make_request('POST', '/invoices', invoice_data)
        if response and response.status_code == 200:
            invoice = response.json()
            self.created_resources['invoices'].append(invoice['id'])
            
            if invoice['payment_method'] == "كاش 0100":
                self.log_result(
                    "إنشاء فاتورة بطريقة دفع كاش 0100",
                    True,
                    f"تم إنشاء الفاتورة {invoice['invoice_number']} بطريقة الدفع الجديدة"
                )
            else:
                self.log_result(
                    "إنشاء فاتورة بطريقة دفع كاش 0100",
                    False,
                    f"طريقة الدفع المحفوظة: {invoice['payment_method']}"
                )
        else:
            self.log_result(
                "إنشاء فاتورة بطريقة دفع كاش 0100",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )

    def test_payment_method_conversion(self):
        """اختبار نظام تغيير طرق الدفع في الفواتير"""
        print("🧪 اختبار 2: نظام تغيير طرق الدفع في الفواتير")
        
        # إنشاء فاتورة نقدية للاختبار
        invoice_data = {
            "customer_name": "عميل اختبار تحويل الدفع",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "BUR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 10.0,
                    "quantity": 3,
                    "unit_price": 15.0,
                    "total_price": 45.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي"
        }
        
        response = self.make_request('POST', '/invoices', invoice_data)
        if response and response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['id']
            self.created_resources['invoices'].append(invoice_id)
            
            # اختبار تحويل من نقدي إلى فودافون 010
            response = self.make_request(
                'PUT', 
                f'/invoices/{invoice_id}/change-payment-method',
                params={'new_payment_method': 'فودافون 010'}
            )
            
            if response and response.status_code == 200:
                result = response.json()
                
                # التحقق من تحديث الفاتورة
                invoice_response = self.make_request('GET', f'/invoices/{invoice_id}')
                if invoice_response and invoice_response.status_code == 200:
                    updated_invoice = invoice_response.json()
                    
                    if updated_invoice['payment_method'] == 'فودافون 010':
                        self.log_result(
                            "تحويل طريقة الدفع من نقدي إلى فودافون 010",
                            True,
                            f"تم التحويل بنجاح - المبلغ: {result.get('amount_transferred', 0)} ج.م"
                        )
                    else:
                        self.log_result(
                            "تحويل طريقة الدفع من نقدي إلى فودافون 010",
                            False,
                            f"طريقة الدفع لم تتغير: {updated_invoice['payment_method']}"
                        )
                else:
                    self.log_result(
                        "تحويل طريقة الدفع من نقدي إلى فودافون 010",
                        False,
                        error="فشل في استرجاع الفاتورة المحدثة"
                    )
            else:
                self.log_result(
                    "تحويل طريقة الدفع من نقدي إلى فودافون 010",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
            
            # اختبار تحويل إلى كاش 0100
            response = self.make_request(
                'PUT',
                f'/invoices/{invoice_id}/change-payment-method',
                params={'new_payment_method': 'كاش 0100'}
            )
            
            if response and response.status_code == 200:
                self.log_result(
                    "تحويل طريقة الدفع إلى كاش 0100",
                    True,
                    "تم التحويل بنجاح"
                )
            else:
                self.log_result(
                    "تحويل طريقة الدفع إلى كاش 0100",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
                
            # اختبار تحويل إلى انستاباي
            response = self.make_request(
                'PUT',
                f'/invoices/{invoice_id}/change-payment-method',
                params={'new_payment_method': 'انستاباي'}
            )
            
            if response and response.status_code == 200:
                self.log_result(
                    "تحويل طريقة الدفع إلى انستاباي",
                    True,
                    "تم التحويل بنجاح"
                )
            else:
                self.log_result(
                    "تحويل طريقة الدفع إلى انستاباي",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
                
            # اختبار تحويل إلى يد الصاوي
            response = self.make_request(
                'PUT',
                f'/invoices/{invoice_id}/change-payment-method',
                params={'new_payment_method': 'يد الصاوي'}
            )
            
            if response and response.status_code == 200:
                self.log_result(
                    "تحويل طريقة الدفع إلى يد الصاوي",
                    True,
                    "تم التحويل بنجاح"
                )
            else:
                self.log_result(
                    "تحويل طريقة الدفع إلى يد الصاوي",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
                
            # اختبار تحويل إلى آجل
            response = self.make_request(
                'PUT',
                f'/invoices/{invoice_id}/change-payment-method',
                params={'new_payment_method': 'آجل'}
            )
            
            if response and response.status_code == 200:
                self.log_result(
                    "تحويل طريقة الدفع إلى آجل",
                    True,
                    "تم التحويل بنجاح"
                )
            else:
                self.log_result(
                    "تحويل طريقة الدفع إلى آجل",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
        else:
            self.log_result(
                "إنشاء فاتورة لاختبار تحويل الدفع",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )

    def test_treasury_update_on_payment_conversion(self):
        """اختبار تحديث الخزينة عند تغيير طريقة الدفع"""
        print("🧪 اختبار 3: تحديث الخزينة عند تغيير طريقة الدفع")
        
        # الحصول على أرصدة الخزينة قبل التحويل
        response = self.make_request('GET', '/treasury/balances')
        if response and response.status_code == 200:
            balances_before = response.json()
            cash_before = balances_before.get('cash', 0)
            vodafone_before = balances_before.get('vodafone_elsawy', 0)
            
            # إنشاء فاتورة نقدية
            invoice_data = {
                "customer_name": "عميل اختبار الخزينة",
                "items": [
                    {
                        "seal_type": "B17",
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 30.0,
                        "height": 6.0,
                        "quantity": 2,
                        "unit_price": 20.0,
                        "total_price": 40.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": "نقدي"
            }
            
            response = self.make_request('POST', '/invoices', invoice_data)
            if response and response.status_code == 200:
                invoice = response.json()
                invoice_id = invoice['id']
                invoice_amount = invoice['total_amount']
                self.created_resources['invoices'].append(invoice_id)
                
                # تحويل إلى فودافون 010
                response = self.make_request(
                    'PUT',
                    f'/invoices/{invoice_id}/change-payment-method',
                    params={'new_payment_method': 'فودافون 010'}
                )
                
                if response and response.status_code == 200:
                    # التحقق من تحديث الخزينة
                    time.sleep(1)  # انتظار قصير لضمان تحديث البيانات
                    
                    response = self.make_request('GET', '/treasury/balances')
                    if response and response.status_code == 200:
                        balances_after = response.json()
                        cash_after = balances_after.get('cash', 0)
                        vodafone_after = balances_after.get('vodafone_elsawy', 0)
                        
                        # التحقق من التغييرات المتوقعة
                        expected_cash_change = -invoice_amount  # خصم من النقدي
                        expected_vodafone_change = invoice_amount  # إضافة للفودافون
                        
                        cash_change = cash_after - cash_before
                        vodafone_change = vodafone_after - vodafone_before
                        
                        if (abs(cash_change - expected_cash_change) < 0.01 and 
                            abs(vodafone_change - expected_vodafone_change) < 0.01):
                            self.log_result(
                                "تحديث الخزينة عند تحويل الدفع",
                                True,
                                f"النقدي: {cash_change:.2f} ج.م، فودافون: {vodafone_change:.2f} ج.م"
                            )
                        else:
                            self.log_result(
                                "تحديث الخزينة عند تحويل الدفع",
                                False,
                                f"التغيير الفعلي - النقدي: {cash_change:.2f}، فودافون: {vodafone_change:.2f}"
                            )
                    else:
                        self.log_result(
                            "تحديث الخزينة عند تحويل الدفع",
                            False,
                            error="فشل في الحصول على أرصدة الخزينة بعد التحويل"
                        )
                else:
                    self.log_result(
                        "تحديث الخزينة عند تحويل الدفع",
                        False,
                        error="فشل في تحويل طريقة الدفع"
                    )
            else:
                self.log_result(
                    "تحديث الخزينة عند تحويل الدفع",
                    False,
                    error="فشل في إنشاء الفاتورة"
                )
        else:
            self.log_result(
                "تحديث الخزينة عند تحويل الدفع",
                False,
                error="فشل في الحصول على أرصدة الخزينة الأولية"
            )

    def test_invoice_cancellation_system(self):
        """اختبار نظام إلغاء الفواتير"""
        print("🧪 اختبار 4: نظام إلغاء الفواتير")
        
        # الحصول على المواد الخام قبل الإلغاء
        response = self.make_request('GET', '/raw-materials')
        if response and response.status_code == 200:
            materials_before = response.json()
            
            # إنشاء فاتورة مصنعة للاختبار
            invoice_data = {
                "customer_name": "عميل اختبار الإلغاء",
                "items": [
                    {
                        "seal_type": "RSE",
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 30.0,
                        "height": 8.0,
                        "quantity": 4,
                        "unit_price": 12.0,
                        "total_price": 48.0,
                        "product_type": "manufactured",
                        "material_details": {
                            "material_type": "NBR",
                            "inner_diameter": 20.0,
                            "outer_diameter": 30.0,
                            "unit_code": "N-1"
                        }
                    }
                ],
                "payment_method": "فودافون 010"
            }
            
            response = self.make_request('POST', '/invoices', invoice_data)
            if response and response.status_code == 200:
                invoice = response.json()
                invoice_id = invoice['id']
                invoice_number = invoice['invoice_number']
                
                # اختبار إلغاء الفاتورة
                response = self.make_request('DELETE', f'/invoices/{invoice_id}/cancel')
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    # التحقق من حذف الفاتورة
                    response = self.make_request('GET', f'/invoices/{invoice_id}')
                    if response and response.status_code == 404:
                        self.log_result(
                            "حذف الفاتورة من النظام",
                            True,
                            f"تم حذف الفاتورة {invoice_number} بنجاح"
                        )
                    else:
                        self.log_result(
                            "حذف الفاتورة من النظام",
                            False,
                            "الفاتورة ما زالت موجودة في النظام"
                        )
                    
                    # التحقق من استرداد المواد
                    response = self.make_request('GET', '/raw-materials')
                    if response and response.status_code == 200:
                        materials_after = response.json()
                        
                        # البحث عن المادة المستخدمة
                        material_found = False
                        for material in materials_after:
                            if (material.get('material_type') == 'NBR' and
                                material.get('inner_diameter') == 20.0 and
                                material.get('outer_diameter') == 30.0):
                                
                                # حساب المادة المتوقع استردادها
                                expected_restoration = 4 * (8 + 2)  # 4 سيل × (8 + 2) مم
                                
                                # مقارنة مع المادة قبل الإنشاء
                                for old_material in materials_before:
                                    if (old_material.get('id') == material.get('id')):
                                        height_difference = material.get('height', 0) - old_material.get('height', 0)
                                        
                                        if abs(height_difference) < 0.01:  # تقريباً نفس الارتفاع
                                            self.log_result(
                                                "استرداد المواد للمخزن",
                                                True,
                                                f"تم استرداد المواد بنجاح - المادة: {material.get('unit_code')}"
                                            )
                                            material_found = True
                                            break
                                break
                        
                        if not material_found:
                            self.log_result(
                                "استرداد المواد للمخزن",
                                False,
                                "لم يتم العثور على دليل على استرداد المواد"
                            )
                    
                    # التحقق من المعاملة العكسية في الخزينة
                    response = self.make_request('GET', '/treasury/transactions')
                    if response and response.status_code == 200:
                        transactions = response.json()
                        
                        # البحث عن معاملة الإلغاء
                        cancellation_found = False
                        for transaction in transactions:
                            if (f"إلغاء-{invoice_number}" in transaction.get('reference', '') or
                                f"إلغاء فاتورة {invoice_number}" in transaction.get('description', '')):
                                cancellation_found = True
                                break
                        
                        if cancellation_found:
                            self.log_result(
                                "المعاملة العكسية في الخزينة",
                                True,
                                f"تم إنشاء معاملة عكسية لإلغاء الفاتورة {invoice_number}"
                            )
                        else:
                            self.log_result(
                                "المعاملة العكسية في الخزينة",
                                False,
                                "لم يتم العثور على معاملة عكسية في الخزينة"
                            )
                    
                    self.log_result(
                        "إلغاء الفاتورة الإجمالي",
                        True,
                        f"تم إلغاء الفاتورة {invoice_number} بنجاح مع جميع العمليات المطلوبة"
                    )
                else:
                    self.log_result(
                        "إلغاء الفاتورة",
                        False,
                        error=f"HTTP {response.status_code if response else 'No Response'}"
                    )
            else:
                self.log_result(
                    "إنشاء فاتورة لاختبار الإلغاء",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
        else:
            self.log_result(
                "الحصول على المواد الخام قبل الاختبار",
                False,
                error="فشل في الحصول على المواد الخام"
            )

    def test_cancel_different_invoice_types(self):
        """اختبار إلغاء أنواع مختلفة من الفواتير"""
        print("🧪 اختبار 5: إلغاء أنواع مختلفة من الفواتير")
        
        # اختبار إلغاء فاتورة محلية
        invoice_data = {
            "customer_name": "عميل اختبار إلغاء محلي",
            "items": [
                {
                    "product_name": "منتج محلي للاختبار",
                    "quantity": 2,
                    "unit_price": 25.0,
                    "total_price": 50.0,
                    "product_type": "local",
                    "supplier": "مورد اختبار",
                    "purchase_price": 20.0,
                    "selling_price": 25.0
                }
            ],
            "payment_method": "كاش 0100"
        }
        
        response = self.make_request('POST', '/invoices', invoice_data)
        if response and response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['id']
            
            response = self.make_request('DELETE', f'/invoices/{invoice_id}/cancel')
            if response and response.status_code == 200:
                self.log_result(
                    "إلغاء فاتورة محلية",
                    True,
                    f"تم إلغاء الفاتورة المحلية {invoice['invoice_number']} بنجاح"
                )
            else:
                self.log_result(
                    "إلغاء فاتورة محلية",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
        
        # اختبار إلغاء فاتورة آجلة
        invoice_data = {
            "customer_name": "عميل اختبار إلغاء آجل",
            "items": [
                {
                    "seal_type": "B3",
                    "material_type": "BUR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 12.0,
                    "quantity": 3,
                    "unit_price": 18.0,
                    "total_price": 54.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "آجل"
        }
        
        response = self.make_request('POST', '/invoices', invoice_data)
        if response and response.status_code == 200:
            invoice = response.json()
            invoice_id = invoice['id']
            
            response = self.make_request('DELETE', f'/invoices/{invoice_id}/cancel')
            if response and response.status_code == 200:
                self.log_result(
                    "إلغاء فاتورة آجلة",
                    True,
                    f"تم إلغاء الفاتورة الآجلة {invoice['invoice_number']} بنجاح"
                )
            else:
                self.log_result(
                    "إلغاء فاتورة آجلة",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )

    def cleanup_test_data(self):
        """تنظيف البيانات المنشأة أثناء الاختبار"""
        print("🧹 تنظيف بيانات الاختبار...")
        
        # حذف الفواتير المنشأة (التي لم يتم إلغاؤها)
        for invoice_id in self.created_resources['invoices']:
            response = self.make_request('DELETE', f'/invoices/{invoice_id}')
            if response and response.status_code == 200:
                print(f"✅ تم حذف الفاتورة {invoice_id}")
        
        # حذف العملاء المنشأين
        for customer_id in self.created_resources['customers']:
            response = self.make_request('DELETE', f'/customers/{customer_id}')
            if response and response.status_code == 200:
                print(f"✅ تم حذف العميل {customer_id}")
        
        # حذف المواد الخام المنشأة
        for material_id in self.created_resources['raw_materials']:
            response = self.make_request('DELETE', f'/raw-materials/{material_id}')
            if response and response.status_code == 200:
                print(f"✅ تم حذف المادة الخام {material_id}")
        
        # حذف عناصر الجرد المنشأة
        for item_id in self.created_resources['inventory_items']:
            response = self.make_request('DELETE', f'/inventory/{item_id}')
            if response and response.status_code == 200:
                print(f"✅ تم حذف عنصر الجرد {item_id}")

    def generate_summary(self):
        """إنشاء ملخص نتائج الاختبار"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("📊 ملخص نتائج اختبار الميزات الجديدة")
        print("="*80)
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"الاختبارات الناجحة: {passed_tests}")
        print(f"الاختبارات الفاشلة: {failed_tests}")
        print(f"معدل النجاح: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}")
                    if result['error']:
                        print(f"    الخطأ: {result['error']}")
            print()
        
        print("✅ الاختبارات الناجحة:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }

    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء اختبار الميزات الجديدة المطلوبة من المستخدم")
        print("="*80)
        
        # إعداد البيانات الأساسية
        if not self.setup_test_data():
            print("❌ فشل في إعداد البيانات الأساسية - توقف الاختبار")
            return
        
        try:
            # تشغيل الاختبارات
            self.test_payment_method_names_update()
            self.test_payment_method_conversion()
            self.test_treasury_update_on_payment_conversion()
            self.test_invoice_cancellation_system()
            self.test_cancel_different_invoice_types()
            
        finally:
            # تنظيف البيانات
            self.cleanup_test_data()
        
        # إنشاء الملخص
        return self.generate_summary()

def main():
    """الدالة الرئيسية"""
    tester = NewFeaturesTester()
    summary = tester.run_all_tests()
    
    # حفظ النتائج في ملف
    with open('/app/test_results_new_features.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 تم حفظ النتائج في: /app/test_results_new_features.json")
    
    return summary['success_rate'] >= 80  # نجح إذا كان معدل النجاح 80% أو أكثر

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)