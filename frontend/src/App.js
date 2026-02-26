import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Company ID mapping for offline fallback
const COMPANY_MAP = {
  "Elsawy": "elsawy",
  "master": "elsawy",
  "Root": "elsawy",
  "Faster": "faster",
};

// Setup axios interceptor to auto-append company_id to all requests
axios.interceptors.request.use((config) => {
  try {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      const companyId = user.company_id || COMPANY_MAP[user.username] || 'elsawy';

      // Add company_id as query parameter
      if (config.params) {
        config.params.company_id = companyId;
      } else {
        config.params = { company_id: companyId };
      }
    }
  } catch (e) {
    // Silently ignore errors
  }
  return config;
});

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [appSettings, setAppSettings] = useState({ currency: 'ج.م', invoice_language: 'ar' });

  const fetchAppSettings = async () => {
    try {
      const res = await axios.get(`${API}/settings`);
      setAppSettings(prev => ({
        ...prev,
        currency: res.data.currency || 'ج.م',
        invoice_language: res.data.invoice_language || 'ar'
      }));
    } catch (e) { console.error('Settings fetch error:', e); }
  };

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      fetchAppSettings();
    }
    setIsLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, null, {
        params: { username, password }
      });

      if (response.data.success) {
        setUser(response.data.user);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        fetchAppSettings();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      // Offline fallback: check credentials locally when backend is unavailable
      const predefinedUsers = {
        "Elsawy": { password: "100100", role: "admin", company_id: "elsawy" },
        "master": { password: "146200", role: "master", company_id: "elsawy" },
        "Root": { password: "master", role: "user", company_id: "elsawy" },
        "Faster": { password: "100200", role: "admin", company_id: "faster" },
      };
      if (predefinedUsers[username] && predefinedUsers[username].password === password) {
        const offlineUser = { username, role: predefinedUsers[username].role, company_id: predefinedUsers[username].company_id };
        setUser(offlineUser);
        localStorage.setItem('user', JSON.stringify(offlineUser));
        return true;
      }
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-xl">جاري التحميل...</div>
    </div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, appSettings, setAppSettings, fetchAppSettings }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const success = await login(username, password);
    if (!success) {
      setError('خطأ في اسم المستخدم أو كلمة المرور');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex items-center justify-center p-4" dir="rtl">
      <div className="max-w-md w-full">
        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-blue-100">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="mb-4">
              <img
                src="https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg"
                alt="Master Seal Logo"
                className="h-16 w-16 mx-auto rounded-full shadow-lg border-4 border-blue-100"
              />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">ماستر سيل</h1>
            <p className="text-gray-500 mt-2">نظام إدارة الشركة المتكامل</p>
            <div className="w-16 h-1 bg-gradient-to-r from-blue-400 to-blue-600 mx-auto mt-3 rounded-full"></div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                👤 اسم المستخدم
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-3 focus:ring-blue-200 focus:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-white"
                placeholder="ادخل اسم المستخدم"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                🔒 كلمة المرور
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-3 focus:ring-blue-200 focus:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-white"
                placeholder="ادخل كلمة المرور"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm text-center animate-pulse">
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 to-blue-800 text-white py-3 px-6 rounded-xl hover:from-blue-700 hover:to-blue-900 focus:outline-none focus:ring-3 focus:ring-blue-300 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              🚀 دخول
            </button>
          </form>

          {/* Footer */}
          <div className="text-center mt-8 pt-6 border-t border-gray-100">
            <p className="text-xs text-gray-400">الحرفيين - السلام - أمام السوبر جيت</p>
            <p className="text-xs text-gray-500 mt-1 font-medium">📞 01020630677</p>
          </div>
        </div>

        {/* Additional Info Card */}
        <div className="mt-6 bg-white/60 backdrop-blur-sm rounded-xl p-4 text-center border border-blue-100/50">
          <p className="text-sm text-gray-600">نظام إدارة متكامل لإدارة المبيعات والمخزون والحسابات</p>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ currentPage, onPageChange }) => {
  const { user, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sidebarSettings, setSidebarSettings] = useState({
    company_name: 'ماستر سيل',
    system_subtitle: 'نظام إدارة متكامل',
    company_address: 'الحرفيين - السلام - أمام السوبر جيت',
    company_phone: '٠١٠٢٠٦٣٠٦٧٧',
    logo_url: 'https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg'
  });

  useEffect(() => {
    const fetchSidebarSettings = async () => {
      try {
        const response = await axios.get(`${API}/settings`);
        setSidebarSettings(prev => ({ ...prev, ...response.data }));
      } catch (error) {
        console.error('Error fetching sidebar settings:', error);
      }
    };
    fetchSidebarSettings();
  }, [currentPage]); // re-fetch when navigating (catches settings page saves)

  // Master user has all pages + delete records
  const masterPages = [
    { key: 'dashboard', label: 'لوحة التحكم', icon: '📊' },
    { key: 'daily-sales', label: 'كشف مبيعات يومي', icon: '📋' },
    { key: 'sales', label: 'المبيعات', icon: '💰' },
    { key: 'inventory', label: 'المخزن الخامات', icon: '📦' },
    { key: 'stock', label: 'مخزن إنتاج', icon: '🏪' },
    { key: 'local', label: 'موردين', icon: '🏭' },
    { key: 'deferred', label: 'الآجل', icon: '⏳' },
    { key: 'expenses', label: 'المصروفات', icon: '💸' },
    { key: 'revenue', label: 'الإيرادات', icon: '📈' },
    { key: 'treasury', label: 'الخزينة', icon: '🏦' },
    { key: 'main-treasury', label: 'الخزنة الرئيسية', icon: '🔐' },
    { key: 'invoices', label: 'الفواتير', icon: '🧾' },
    { key: 'deleted-invoices', label: 'الفواتير المحذوفة', icon: '🗑️' },
    { key: 'customer-statement', label: 'كشف الحساب', icon: '📋' },
    { key: 'settle-account', label: 'تصفية حساب', icon: '💵' },
    { key: 'work-orders', label: 'أمر شغل', icon: '⚙️' },
    { key: 'customers', label: 'إدارة العملاء', icon: '👥' },
    { key: 'pricing', label: 'التسعير', icon: '💲' },
    { key: 'backup', label: 'النسخ الاحتياطي', icon: '💾' },
    { key: 'users', label: 'المستخدمين', icon: '👥' },
    { key: 'settings', label: 'الضبط', icon: '⚙️' }
  ];

  // Dashboard is only for Elsawy
  const elsawyPages = [
    { key: 'dashboard', label: 'لوحة التحكم', icon: '📊' },
    { key: 'daily-sales', label: 'كشف مبيعات يومي', icon: '📋' },
    { key: 'sales', label: 'المبيعات', icon: '💰' },
    { key: 'inventory', label: 'المخزن الخامات', icon: '📦' },
    { key: 'stock', label: 'مخزن إنتاج', icon: '🏪' },
    { key: 'local', label: 'موردين', icon: '🏭' },
    { key: 'deferred', label: 'الآجل', icon: '⏳' },
    { key: 'expenses', label: 'المصروفات', icon: '💸' },
    { key: 'revenue', label: 'الإيرادات', icon: '📈' },
    { key: 'treasury', label: 'الخزينة', icon: '🏦' },
    { key: 'main-treasury', label: 'الخزنة الرئيسية', icon: '🔐' },
    { key: 'invoices', label: 'الفواتير', icon: '🧾' },
    { key: 'deleted-invoices', label: 'الفواتير المحذوفة', icon: '🗑️' },
    { key: 'customer-statement', label: 'كشف الحساب', icon: '📋' },
    { key: 'settle-account', label: 'تصفية حساب', icon: '💵' },
    { key: 'work-orders', label: 'أمر شغل', icon: '⚙️' },
    { key: 'customers', label: 'إدارة العملاء', icon: '👥' },
    { key: 'pricing', label: 'التسعير', icon: '💲' },
    { key: 'backup', label: 'النسخ الاحتياطي', icon: '💾' },
    { key: 'users', label: 'المستخدمين', icon: '👥' },
    { key: 'settings', label: 'الضبط', icon: '⚙️' }
  ];

  const adminPages = [
    { key: 'dashboard', label: 'لوحة التحكم', icon: '📊' },
    { key: 'daily-sales', label: 'كشف مبيعات يومي', icon: '📋' },
    { key: 'sales', label: 'المبيعات', icon: '💰' },
    { key: 'inventory', label: 'المخزن الخامات', icon: '📦' },
    { key: 'stock', label: 'مخزن إنتاج', icon: '🏪' },
    { key: 'local', label: 'موردين', icon: '🏭' },
    { key: 'deferred', label: 'الآجل', icon: '⏳' },
    { key: 'expenses', label: 'المصروفات', icon: '💸' },
    { key: 'revenue', label: 'الإيرادات', icon: '📈' },
    { key: 'treasury', label: 'الخزينة', icon: '🏦' },
    { key: 'main-treasury', label: 'الخزنة الرئيسية', icon: '🔐' },
    { key: 'invoices', label: 'الفواتير', icon: '🧾' },
    { key: 'deleted-invoices', label: 'الفواتير المحذوفة', icon: '🗑️' },
    { key: 'customer-statement', label: 'كشف الحساب', icon: '📋' },
    { key: 'settle-account', label: 'تصفية حساب', icon: '💵' },
    { key: 'work-orders', label: 'أمر شغل', icon: '⚙️' },
    { key: 'customers', label: 'إدارة العملاء', icon: '👥' },
    { key: 'pricing', label: 'التسعير', icon: '💲' },
    { key: 'backup', label: 'النسخ الاحتياطي', icon: '💾' },
    { key: 'users', label: 'المستخدمين', icon: '👥' },
    { key: 'settings', label: 'الضبط', icon: '⚙️' }
  ];

  const userPages = [
    { key: 'daily-sales', label: 'كشف مبيعات يومي', icon: '📋' },
    { key: 'sales', label: 'المبيعات', icon: '💰' },
    { key: 'inventory', label: 'المخزن الخامات', icon: '📦' },
    { key: 'stock', label: 'مخزن إنتاج', icon: '🏪' },
    { key: 'local', label: 'موردين', icon: '🏭' },
    { key: 'deferred', label: 'الآجل', icon: '⏳' },
    { key: 'expenses', label: 'المصروفات', icon: '💸' },
    { key: 'treasury', label: 'الخزينة', icon: '🏦' },
    { key: 'invoices', label: 'الفواتير', icon: '🧾' },
    { key: 'deleted-invoices', label: 'الفواتير المحذوفة', icon: '🗑️' },
    { key: 'customer-statement', label: 'كشف الحساب', icon: '📋' },
    { key: 'work-orders', label: 'أمر شغل', icon: '⚙️' },
    { key: 'pricing', label: 'التسعير', icon: '💲' }
  ];

  // Determine pages based on user role
  const pages = user?.username === 'master' ? masterPages :
    user?.username === 'Elsawy' ? elsawyPages :
      user?.role === 'admin' ? adminPages : userPages;

  return (
    <div
      className={`bg-gradient-to-b from-blue-900 via-blue-800 to-blue-900 text-white shadow-2xl transition-all duration-300 relative ${isCollapsed ? 'w-20' : 'w-80'
        }`}
    >
      {/* Collapse/Expand Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -left-4 top-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-2 shadow-lg z-50 transition-all"
        title={isCollapsed ? 'توسيع القائمة' : 'طي القائمة'}
      >
        <span className="text-xl">{isCollapsed ? '◀' : '▶'}</span>
      </button>

      {/* Header */}
      <div className="p-6 border-b border-blue-700">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3 space-x-reverse'}`}>
          <img
            src={sidebarSettings.logo_url}
            alt="Logo"
            className="h-12 w-12 rounded-lg shadow-lg"
          />
          {!isCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-white">{sidebarSettings.company_name}</h1>
              <p className="text-xs text-blue-200">{sidebarSettings.system_subtitle}</p>
            </div>
          )}
        </div>
      </div>

      {/* User Info */}
      <div className="p-4 bg-blue-800 border-b border-blue-700">
        <div className={`flex items-center ${isCollapsed ? 'justify-center flex-col space-y-2' : 'justify-between'}`}>
          {!isCollapsed && (
            <div>
              <p className="text-sm font-medium">أهلاً وسهلاً</p>
              <p className="text-lg font-bold text-blue-200">{user?.username}</p>
            </div>
          )}
          <button
            onClick={logout}
            className={`bg-red-500 hover:bg-red-600 rounded-lg text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl ${isCollapsed ? 'p-2' : 'px-3 py-2'
              }`}
            title="خروج"
          >
            {isCollapsed ? '🚪' : 'خروج'}
          </button>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
        {pages.map(page => (
          <button
            key={page.key}
            onClick={() => onPageChange(page.key)}
            className={`w-full flex items-center p-4 rounded-xl transition-all duration-200 group ${isCollapsed ? 'justify-center' : 'space-x-3 space-x-reverse text-right'
              } ${currentPage === page.key
                ? 'bg-white text-blue-900 shadow-lg transform scale-105'
                : 'hover:bg-blue-700 hover:transform hover:translate-x-2'
              }`}
            title={isCollapsed ? page.label : ''}
          >
            <span className="text-2xl">{page.icon}</span>
            {!isCollapsed && (
              <>
                <span className="font-medium">{page.label}</span>
                {currentPage === page.key && (
                  <div className="mr-auto">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  </div>
                )}
              </>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-blue-700 text-center">
          <p className="text-xs text-blue-300">{sidebarSettings.company_address}</p>
          <p className="text-xs text-blue-400 mt-1">{sidebarSettings.company_phone}</p>
        </div>
      )}
    </div>
  );
};

// Inventory Management Component
const Inventory = () => {
  const [inventoryItems, setInventoryItems] = useState([]);
  const [inventoryTransactions, setInventoryTransactions] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [currentView, setCurrentView] = useState('items'); // items, transactions, low-stock, add-item
  const [editingItem, setEditingItem] = useState(null); // للتعديل
  const [newItem, setNewItem] = useState({
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    available_pieces: '',  // تغيير من available_height إلى available_pieces
    min_stock_level: 2,    // الحد الأدنى 2 قطعة
    notes: ''
  });
  const [newTransaction, setNewTransaction] = useState({
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    transaction_type: 'in',
    pieces_change: '',     // تغيير من height_change إلى pieces_change
    reason: '',
    notes: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  const materialTypes = ['NBR', 'BUR', 'BT', 'VT', 'BOOM'];

  // Fetch functions
  const fetchInventoryItems = async () => {
    try {
      const response = await axios.get(`${API}/inventory`);
      setInventoryItems(response.data || []);
    } catch (error) {
      console.error('Error fetching inventory items:', error);
    }
  };

  const fetchInventoryTransactions = async () => {
    try {
      const response = await axios.get(`${API}/inventory-transactions`);
      setInventoryTransactions(response.data || []);
    } catch (error) {
      console.error('Error fetching inventory transactions:', error);
    }
  };

  const fetchLowStockItems = async () => {
    try {
      const response = await axios.get(`${API}/inventory/low-stock`);
      setLowStockItems(response.data || []);
    } catch (error) {
      console.error('Error fetching low stock items:', error);
    }
  };

  useEffect(() => {
    fetchInventoryItems();
    fetchInventoryTransactions();
    fetchLowStockItems();
  }, []);

  // Add or Update inventory item
  const addInventoryItem = async () => {
    if (!newItem.material_type || !newItem.inner_diameter ||
      !newItem.outer_diameter || !newItem.available_pieces) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      if (editingItem) {
        // Update existing item
        await axios.put(`${API}/inventory/${editingItem.id}`, {
          ...newItem,
          inner_diameter: parseFloat(newItem.inner_diameter),
          outer_diameter: parseFloat(newItem.outer_diameter),
          available_pieces: parseInt(newItem.available_pieces),
          min_stock_level: parseInt(newItem.min_stock_level || 2)
        });
        alert('تم تحديث عنصر الجرد بنجاح');
        setEditingItem(null);
      } else {
        // Add new item
        await axios.post(`${API}/inventory`, {
          ...newItem,
          inner_diameter: parseFloat(newItem.inner_diameter),
          outer_diameter: parseFloat(newItem.outer_diameter),
          available_pieces: parseInt(newItem.available_pieces),
          min_stock_level: parseInt(newItem.min_stock_level || 2)
        });
        alert('تم إضافة عنصر الجرد بنجاح');
      }

      fetchInventoryItems();
      fetchLowStockItems();
      setCurrentView('items');
      setNewItem({
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        available_pieces: '',
        min_stock_level: 2,
        notes: ''
      });
    } catch (error) {
      console.error('Error saving inventory item:', error);
      alert('حدث خطأ في حفظ عنصر الجرد: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Add inventory transaction
  const addInventoryTransaction = async () => {
    if (!newTransaction.material_type || !newTransaction.inner_diameter ||
      !newTransaction.outer_diameter || !newTransaction.pieces_change || !newTransaction.reason) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      const transactionData = {
        ...newTransaction,
        inner_diameter: parseFloat(newTransaction.inner_diameter),
        outer_diameter: parseFloat(newTransaction.outer_diameter),
        pieces_change: newTransaction.transaction_type === 'out'
          ? -Math.abs(parseInt(newTransaction.pieces_change))
          : Math.abs(parseInt(newTransaction.pieces_change))
      };

      await axios.post(`${API}/inventory-transactions`, transactionData);

      fetchInventoryItems();
      fetchInventoryTransactions();
      fetchLowStockItems();
      setNewTransaction({
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        transaction_type: 'in',
        pieces_change: '',
        reason: '',
        notes: ''
      });
      alert('تم تسجيل معاملة الجرد بنجاح');
    } catch (error) {
      console.error('Error adding inventory transaction:', error);
      alert('حدث خطأ في تسجيل معاملة الجرد: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Filter and sort items based on search
  const filteredItems = inventoryItems.filter(item =>
    item.material_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.inner_diameter.toString().includes(searchTerm.toLowerCase()) ||
    item.outer_diameter.toString().includes(searchTerm.toLowerCase()) ||
    item.notes?.toLowerCase().includes(searchTerm.toLowerCase())
  ).sort((a, b) => {
    // ترتيب حسب أولوية الخامة: BUR-NBR-BT-BOOM-VT
    const materialPriority = { 'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5 };
    const aPriority = materialPriority[a.material_type] || 6;
    const bPriority = materialPriority[b.material_type] || 6;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }
    // ثم ترتيب حسب المقاس (القطر الداخلي ثم الخارجي)
    if (a.inner_diameter !== b.inner_diameter) {
      return a.inner_diameter - b.inner_diameter;
    }
    return a.outer_diameter - b.outer_diameter;
  });

  const filteredTransactions = inventoryTransactions.filter(transaction =>
    transaction.reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.material_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.notes?.toLowerCase().includes(searchTerm.toLowerCase())
  ).sort((a, b) => {
    // ترتيب حسب أولوية الخامة: BUR-NBR-BT-BOOM-VT
    const materialPriority = { 'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5 };
    const aPriority = materialPriority[a.material_type] || 6;
    const bPriority = materialPriority[b.material_type] || 6;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }
    // ثم ترتيب حسب المقاس (القطر الداخلي ثم الخارجي) ثم التاريخ
    if (a.inner_diameter !== b.inner_diameter) {
      return a.inner_diameter - b.inner_diameter;
    }
    if (a.outer_diameter !== b.outer_diameter) {
      return a.outer_diameter - b.outer_diameter;
    }
    return new Date(b.date) - new Date(a.date); // الأحدث أولاً
  });

  return (
    <div className="p-6" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">المخزن الخامات</h1>
        <div className="flex space-x-4 space-x-reverse">
          <button
            onClick={() => setCurrentView('items')}
            className={`px-4 py-2 rounded ${currentView === 'items' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            عناصر الجرد
          </button>
          <button
            onClick={() => setCurrentView('transactions')}
            className={`px-4 py-2 rounded ${currentView === 'transactions' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            معاملات الجرد
          </button>
          <button
            onClick={() => setCurrentView('low-stock')}
            className={`px-4 py-2 rounded ${currentView === 'low-stock' ? 'bg-red-500 text-white' : 'bg-gray-200'}`}
          >
            مخزون منخفض ({lowStockItems.length})
          </button>
          <button
            onClick={() => setCurrentView('excel')}
            className={`px-4 py-2 rounded ${currentView === 'excel' ? 'bg-green-500 text-white' : 'bg-gray-200'}`}
          >
            إدارة الإكسل
          </button>
          <button
            onClick={() => setCurrentView('add-item')}
            className={`px-4 py-2 rounded ${currentView === 'add-item' ? 'bg-green-500 text-white' : 'bg-gray-200'}`}
          >
            إضافة عنصر جديد
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="البحث في الجرد..."
          className="w-full p-3 border border-gray-300 rounded-lg"
        />
      </div>

      {/* Inventory Items View */}
      {currentView === 'items' && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">عناصر الجرد</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">نوع المادة</th>
                  <th className="border border-gray-300 p-2">القطر الداخلي</th>
                  <th className="border border-gray-300 p-2">القطر الخارجي</th>
                  <th className="border border-gray-300 p-2">عدد القطع المتاحة</th>
                  <th className="border border-gray-300 p-2">الحد الأدنى</th>
                  <th className="border border-gray-300 p-2">الحالة</th>
                  <th className="border border-gray-300 p-2">ملاحظات</th>
                  <th className="border border-gray-300 p-2">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map(item => (
                  <tr key={item.id}>
                    <td className="border border-gray-300 p-2 font-semibold">{item.material_type}</td>
                    <td className="border border-gray-300 p-2">{item.inner_diameter}</td>
                    <td className="border border-gray-300 p-2">{item.outer_diameter}</td>
                    <td className={`border border-gray-300 p-2 font-semibold ${item.available_pieces <= item.min_stock_level ? 'text-red-600' : 'text-green-600'
                      }`}>
                      {item.available_pieces} قطعة
                    </td>
                    <td className="border border-gray-300 p-2">{item.min_stock_level} قطعة</td>
                    <td className="border border-gray-300 p-2">
                      <span className={`px-2 py-1 rounded text-sm ${item.available_pieces <= item.min_stock_level ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                        }`}>
                        {item.available_pieces <= item.min_stock_level ? 'منخفض' : 'طبيعي'}
                      </span>
                    </td>
                    <td className="border border-gray-300 p-2">{item.notes || '-'}</td>
                    <td className="border border-gray-300 p-2">
                      <div className="flex space-x-2 space-x-reverse">
                        <button
                          onClick={() => {
                            setEditingItem(item);
                            setNewItem({
                              material_type: item.material_type,
                              inner_diameter: item.inner_diameter,
                              outer_diameter: item.outer_diameter,
                              available_pieces: item.available_pieces,
                              min_stock_level: item.min_stock_level,
                              notes: item.notes || ''
                            });
                            setCurrentView('add-item');
                          }}
                          className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                        >
                          تعديل
                        </button>
                        <button
                          onClick={async () => {
                            if (confirm('هل أنت متأكد من حذف هذا العنصر؟')) {
                              try {
                                await axios.delete(`${API}/inventory/${item.id}`);
                                alert('تم حذف العنصر بنجاح');
                                fetchInventoryItems();
                              } catch (error) {
                                console.error('Error deleting item:', error);
                                alert('حدث خطأ في حذف العنصر');
                              }
                            }
                          }}
                          className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                        >
                          حذف
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transactions View */}
      {currentView === 'transactions' && (
        <div>
          {/* Add Transaction Form */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-lg font-semibold mb-4">إضافة معاملة جرد</h3>
            <div className="grid grid-cols-3 gap-4">
              <select
                value={newTransaction.material_type}
                onChange={(e) => setNewTransaction({ ...newTransaction, material_type: e.target.value })}
                className="p-2 border border-gray-300 rounded"
              >
                {materialTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <input
                type="number"
                value={newTransaction.inner_diameter}
                onChange={(e) => setNewTransaction({ ...newTransaction, inner_diameter: e.target.value })}
                placeholder="القطر الداخلي"
                className="p-2 border border-gray-300 rounded"
              />
              <input
                type="number"
                value={newTransaction.outer_diameter}
                onChange={(e) => setNewTransaction({ ...newTransaction, outer_diameter: e.target.value })}
                placeholder="القطر الخارجي"
                className="p-2 border border-gray-300 rounded"
              />
              <select
                value={newTransaction.transaction_type}
                onChange={(e) => setNewTransaction({ ...newTransaction, transaction_type: e.target.value })}
                className="p-2 border border-gray-300 rounded"
              >
                <option value="in">إضافة للمخزون</option>
                <option value="out">خصم من المخزون</option>
              </select>
              <input
                type="number"
                step="1"
                value={newTransaction.pieces_change}
                onChange={(e) => setNewTransaction({ ...newTransaction, pieces_change: e.target.value })}
                placeholder="عدد القطع"
                className="p-2 border border-gray-300 rounded"
              />
              <input
                type="text"
                value={newTransaction.reason}
                onChange={(e) => setNewTransaction({ ...newTransaction, reason: e.target.value })}
                placeholder="سبب المعاملة"
                className="p-2 border border-gray-300 rounded"
              />
            </div>
            <div className="mt-4">
              <input
                type="text"
                value={newTransaction.notes}
                onChange={(e) => setNewTransaction({ ...newTransaction, notes: e.target.value })}
                placeholder="ملاحظات (اختياري)"
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            <button
              onClick={addInventoryTransaction}
              className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              تسجيل المعاملة
            </button>
          </div>

          {/* Transactions List */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">سجل معاملات الجرد</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 p-2">التاريخ</th>
                    <th className="border border-gray-300 p-2">نوع المادة</th>
                    <th className="border border-gray-300 p-2">المقاسات</th>
                    <th className="border border-gray-300 p-2">نوع المعاملة</th>
                    <th className="border border-gray-300 p-2">عدد القطع</th>
                    <th className="border border-gray-300 p-2">الرصيد المتبقي</th>
                    <th className="border border-gray-300 p-2">السبب</th>
                    <th className="border border-gray-300 p-2">ملاحظات</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTransactions.map(transaction => (
                    <tr key={transaction.id}>
                      <td className="border border-gray-300 p-2">
                        {new Date(transaction.date).toLocaleDateString('ar-EG')}
                      </td>
                      <td className="border border-gray-300 p-2">{transaction.material_type}</td>
                      <td className="border border-gray-300 p-2">
                        {transaction.inner_diameter} × {transaction.outer_diameter}
                      </td>
                      <td className="border border-gray-300 p-2">
                        <span className={`px-2 py-1 rounded text-sm ${transaction.transaction_type === 'in'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                          }`}>
                          {transaction.transaction_type === 'in' ? 'إضافة' : 'خصم'}
                        </span>
                      </td>
                      <td className={`border border-gray-300 p-2 font-semibold ${transaction.pieces_change > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                        {transaction.pieces_change > 0 ? '+' : ''}{transaction.pieces_change} قطعة
                      </td>
                      <td className="border border-gray-300 p-2 font-semibold">
                        {transaction.remaining_pieces} قطعة
                      </td>
                      <td className="border border-gray-300 p-2">{transaction.reason}</td>
                      <td className="border border-gray-300 p-2">{transaction.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Low Stock Items View */}
      {currentView === 'low-stock' && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4 text-red-600">
            عناصر بمخزون منخفض ({lowStockItems.length})
          </h3>
          {lowStockItems.length === 0 ? (
            <p className="text-green-600 text-center py-8">
              ✅ جميع عناصر الجرد في المستوى الطبيعي
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-red-50">
                    <th className="border border-gray-300 p-2">نوع المادة</th>
                    <th className="border border-gray-300 p-2">المقاسات</th>
                    <th className="border border-gray-300 p-2">المخزون الحالي</th>
                    <th className="border border-gray-300 p-2">الحد الأدنى</th>
                    <th className="border border-gray-300 p-2">نقص المخزون</th>
                  </tr>
                </thead>
                <tbody>
                  {lowStockItems.map(item => (
                    <tr key={item.id} className="bg-red-50">
                      <td className="border border-gray-300 p-2 font-semibold">{item.material_type}</td>
                      <td className="border border-gray-300 p-2">
                        {item.inner_diameter} × {item.outer_diameter}
                      </td>
                      <td className="border border-gray-300 p-2 font-semibold text-red-600">
                        {item.available_pieces} قطعة
                      </td>
                      <td className="border border-gray-300 p-2">{item.min_stock_level} قطعة</td>
                      <td className="border border-gray-300 p-2 font-semibold text-red-600">
                        {Math.max(0, item.min_stock_level - item.available_pieces)} قطعة
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Add/Edit Item View */}
      {currentView === 'add-item' && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">
            {editingItem ? 'تعديل عنصر الجرد' : 'إضافة عنصر جرد جديد'}
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <select
              value={newItem.material_type}
              onChange={(e) => setNewItem({ ...newItem, material_type: e.target.value })}
              className="p-2 border border-gray-300 rounded"
            >
              {materialTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <input
              type="number"
              value={newItem.inner_diameter}
              onChange={(e) => setNewItem({ ...newItem, inner_diameter: e.target.value })}
              placeholder="القطر الداخلي"
              className="p-2 border border-gray-300 rounded"
            />
            <input
              type="number"
              value={newItem.outer_diameter}
              onChange={(e) => setNewItem({ ...newItem, outer_diameter: e.target.value })}
              placeholder="القطر الخارجي"
              className="p-2 border border-gray-300 rounded"
            />
            <input
              type="number"
              step="1"
              value={newItem.available_pieces}
              onChange={(e) => setNewItem({ ...newItem, available_pieces: e.target.value })}
              placeholder="عدد القطع المتاحة"
              className="p-2 border border-gray-300 rounded"
            />
            <input
              type="number"
              value={newItem.min_stock_level}
              onChange={(e) => setNewItem({ ...newItem, min_stock_level: e.target.value })}
              placeholder="الحد الأدنى للمخزون"
              className="p-2 border border-gray-300 rounded"
            />
            <input
              type="text"
              value={newItem.notes}
              onChange={(e) => setNewItem({ ...newItem, notes: e.target.value })}
              placeholder="ملاحظات (اختياري)"
              className="p-2 border border-gray-300 rounded"
            />
          </div>
          <button
            onClick={addInventoryItem}
            className="mt-4 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            {editingItem ? 'تحديث عنصر الجرد' : 'إضافة عنصر الجرد'}
          </button>
          {editingItem && (
            <button
              onClick={() => {
                setEditingItem(null);
                setNewItem({
                  material_type: 'NBR',
                  inner_diameter: '',
                  outer_diameter: '',
                  available_pieces: '',
                  min_stock_level: 2,
                  notes: ''
                });
                setCurrentView('items');
              }}
              className="mt-4 mr-2 bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              إلغاء التعديل
            </button>
          )}
        </div>
      )}

      {/* Excel Management View */}
      {currentView === 'excel' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Inventory Excel Management */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">إدارة ملفات الجرد - Excel</h3>

            {/* Export Inventory */}
            <div className="mb-6">
              <h4 className="font-medium mb-2">تصدير بيانات الجرد</h4>
              <button
                onClick={async () => {
                  try {
                    const response = await axios.get(`${API}/excel/export/inventory`, {
                      responseType: 'blob'
                    });
                    const url = window.URL.createObjectURL(new Blob([response.data]));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `inventory_export_${new Date().toISOString().split('T')[0]}.xlsx`);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    alert('تم تصدير ملف الجرد بنجاح');
                  } catch (error) {
                    console.error('Error exporting inventory:', error);
                    alert('حدث خطأ في تصدير الملف');
                  }
                }}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                تصدير جرد Excel
              </button>
            </div>

            {/* Import Inventory */}
            <div>
              <h4 className="font-medium mb-2">استيراد بيانات الجرد</h4>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;

                  const formData = new FormData();
                  formData.append('file', file);

                  try {
                    const response = await axios.post(`${API}/excel/import/inventory`, formData, {
                      headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    alert(`تم استيراد ${response.data.imported_count} عنصر بنجاح`);
                    if (response.data.errors.length > 0) {
                      console.warn('Import errors:', response.data.errors);
                    }
                    fetchInventoryItems();
                  } catch (error) {
                    console.error('Error importing inventory:', error);
                    alert('حدث خطأ في استيراد الملف');
                  }

                  e.target.value = '';
                }}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
              <p className="text-sm text-gray-600 mt-2">
                الأعمدة المطلوبة: material_type, inner_diameter, outer_diameter, available_pieces
              </p>
            </div>
          </div>

          {/* Raw Materials Excel Management */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">إدارة المواد الخام - Excel</h3>

            {/* Export Raw Materials */}
            <div className="mb-6">
              <h4 className="font-medium mb-2">تصدير المواد الخام</h4>
              <button
                onClick={async () => {
                  try {
                    const response = await axios.get(`${API}/excel/export/raw-materials`, {
                      responseType: 'blob'
                    });
                    const url = window.URL.createObjectURL(new Blob([response.data]));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `raw_materials_export_${new Date().toISOString().split('T')[0]}.xlsx`);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    alert('تم تصدير ملف المواد الخام بنجاح');
                  } catch (error) {
                    console.error('Error exporting raw materials:', error);
                    alert('حدث خطأ في تصدير الملف');
                  }
                }}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                تصدير مواد خام Excel
              </button>
            </div>

            {/* Import Raw Materials */}
            <div>
              <h4 className="font-medium mb-2">استيراد المواد الخام</h4>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;

                  const formData = new FormData();
                  formData.append('file', file);

                  try {
                    const response = await axios.post(`${API}/excel/import/raw-materials`, formData, {
                      headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    alert(`تم استيراد ${response.data.imported_count} مادة خام بنجاح`);
                    if (response.data.errors.length > 0) {
                      console.warn('Import errors:', response.data.errors);
                    }
                  } catch (error) {
                    console.error('Error importing raw materials:', error);
                    alert('حدث خطأ في استيراد الملف');
                  }

                  e.target.value = '';
                }}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
              <p className="text-sm text-gray-600 mt-2">
                الأعمدة المطلوبة: material_type, inner_diameter, outer_diameter, height, pieces_count, unit_code, cost_per_mm
              </p>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-yellow-50 p-6 rounded-lg shadow-md md:col-span-2">
            <h3 className="text-lg font-semibold mb-4">تعليمات استخدام الإكسل</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">تصدير البيانات:</h4>
                <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                  <li>يتم تصدير جميع البيانات الحالية</li>
                  <li>الملف يحتوي على تنسيق جاهز للتعديل</li>
                  <li>يمكن فتح الملف في Excel أو Google Sheets</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">استيراد البيانات:</h4>
                <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                  <li>يجب أن يكون الملف من نوع .xlsx أو .xls</li>
                  <li>الأعمدة المطلوبة يجب أن تكون موجودة</li>
                  <li>البيانات الموجودة لن تتأثر (يتم التحديث أو الإضافة)</li>
                  <li>سيتم عرض رسالة تأكيد مع عدد العناصر المستوردة</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Local Products Management Component
const Local = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [suppliers, setSuppliers] = useState([]);
  const [localProducts, setLocalProducts] = useState([]);
  const [supplierTransactions, setSupplierTransactions] = useState([]);
  const [currentView, setCurrentView] = useState('suppliers'); // suppliers, products, transactions
  const [newSupplier, setNewSupplier] = useState({ name: '', phone: '', address: '' });
  const [newProduct, setNewProduct] = useState({ name: '', supplier_id: '', purchase_price: '', selling_price: '', current_stock: 0 });
  const [newTransaction, setNewTransaction] = useState({ supplier_id: '', transaction_type: 'purchase', amount: '', description: '', product_name: '', quantity: '', unit_price: '', payment_method: 'cash' });
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');

  // Fetch data functions
  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/suppliers`);
      setSuppliers(response.data || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    }
  };

  const fetchLocalProducts = async () => {
    try {
      const response = await axios.get(`${API}/local-products`);
      setLocalProducts(response.data || []);
    } catch (error) {
      console.error('Error fetching local products:', error);
    }
  };

  const fetchSupplierTransactions = async () => {
    try {
      const response = await axios.get(`${API}/supplier-transactions`);
      setSupplierTransactions(response.data || []);
    } catch (error) {
      console.error('Error fetching supplier transactions:', error);
    }
  };

  // Delete supplier transaction - Master only
  const deleteSupplierTransaction = async (transactionId) => {
    if (user?.username !== 'master') {
      alert('غير مصرح لك بحذف السجلات');
      return;
    }

    // Ask user about deletion type
    const choice = confirm(
      '🗑️ حذف معاملة المورد\n\n' +
      'اختر نوع الحذف:\n\n' +
      '✅ اضغط "موافق" → إلغاء المعاملة وعكس تأثيرها (عكسي)\n' +
      '❌ اضغط "إلغاء" ثم "موافق" → حذف السجل فقط وإعادة حساب الرصيد\n\n' +
      'الخيار الأول (عكسي) ينصح به لضمان دقة الأرصدة'
    );

    if (choice === null) return; // User pressed Escape

    const reverseTransaction = choice;

    // Final confirmation
    const confirmMsg = reverseTransaction
      ? 'تأكيد: سيتم إلغاء المعاملة وعكس تأثيرها على رصيد المورد\n\nهل تريد المتابعة؟'
      : 'تأكيد: سيتم حذف السجل وإعادة حساب رصيد المورد من باقي المعاملات\n\nهل تريد المتابعة؟';

    if (!confirm(confirmMsg)) return;

    try {
      await axios.delete(`${API}/suppliers/transactions/${transactionId}`, {
        params: {
          username: user.username,
          reverse_transaction: reverseTransaction
        }
      });

      alert('✅ تم حذف المعاملة بنجاح');
      fetchSupplierTransactions();
      fetchSuppliers(); // Refresh to update balances
    } catch (error) {
      console.error('Error deleting supplier transaction:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في حذف المعاملة');
    }
  };

  useEffect(() => {
    fetchSuppliers();
    fetchLocalProducts();
    fetchSupplierTransactions();
  }, []);

  // Add supplier
  const addSupplier = async () => {
    if (!newSupplier.name.trim()) {
      alert('الرجاء إدخال اسم المورد');
      return;
    }

    try {
      if (newSupplier.id) {
        // Update existing supplier
        await axios.put(`${API}/suppliers/${newSupplier.id}`, {
          name: newSupplier.name,
          phone: newSupplier.phone,
          address: newSupplier.address
        });
        alert('تم تحديث المورد بنجاح');
      } else {
        // Add new supplier
        await axios.post(`${API}/suppliers`, newSupplier);
        alert('تم إضافة المورد بنجاح');
      }

      fetchSuppliers();
      setNewSupplier({ name: '', phone: '', address: '' });
    } catch (error) {
      console.error('Error saving supplier:', error);
      alert('حدث خطأ في حفظ المورد: ' + (error.response?.data?.detail || error.message));
    }
  };

  const editSupplier = (supplier) => {
    // Fill the form with supplier data for editing
    setNewSupplier({
      id: supplier.id,
      name: supplier.name,
      phone: supplier.phone || '',
      address: supplier.address || ''
    });
  };

  const deleteSupplier = async (supplierId) => {
    if (!confirm('هل أنت متأكد من حذف هذا المورد؟ سيتم حذف جميع البيانات المرتبطة به.')) {
      return;
    }

    try {
      await axios.delete(`${API}/suppliers/${supplierId}`);
      fetchSuppliers();
      fetchLocalProducts(); // Refresh products as they might be affected
      alert('تم حذف المورد بنجاح');
    } catch (error) {
      console.error('Error deleting supplier:', error);
      alert('حدث خطأ في حذف المورد: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Add local product
  const addLocalProduct = async () => {
    if (!newProduct.name.trim() || !newProduct.supplier_id || !newProduct.purchase_price || !newProduct.selling_price) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      if (newProduct.id) {
        // Update existing product
        await axios.put(`${API}/local-products/${newProduct.id}`, {
          name: newProduct.name,
          supplier_id: newProduct.supplier_id,
          purchase_price: parseFloat(newProduct.purchase_price),
          selling_price: parseFloat(newProduct.selling_price),
          current_stock: parseInt(newProduct.current_stock || 0)
        });
        alert('تم تحديث المنتج بنجاح');
      } else {
        // Add new product
        await axios.post(`${API}/local-products`, {
          ...newProduct,
          purchase_price: parseFloat(newProduct.purchase_price),
          selling_price: parseFloat(newProduct.selling_price),
          current_stock: parseInt(newProduct.current_stock || 0)
        });
        alert('تم إضافة المنتج بنجاح');
      }

      fetchLocalProducts();
      setNewProduct({ name: '', supplier_id: '', purchase_price: '', selling_price: '', current_stock: 0 });
    } catch (error) {
      console.error('Error saving local product:', error);
      alert('حدث خطأ في حفظ المنتج: ' + (error.response?.data?.detail || error.message));
    }
  };

  const editLocalProduct = (product) => {
    // Fill the form with product data for editing
    setNewProduct({
      id: product.id,
      name: product.name,
      supplier_id: product.supplier_id,
      purchase_price: product.purchase_price.toString(),
      selling_price: product.selling_price.toString(),
      current_stock: product.current_stock || 0
    });
  };

  const deleteLocalProduct = async (productId) => {
    if (!confirm('هل أنت متأكد من حذف هذا المنتج المحلي؟ سيتم حذف جميع البيانات المرتبطة به.')) {
      return;
    }

    try {
      await axios.delete(`${API}/local-products/${productId}`);
      fetchLocalProducts();
      alert('تم حذف المنتج المحلي بنجاح');
    } catch (error) {
      console.error('Error deleting local product:', error);
      alert('حدث خطأ في حذف المنتج: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Pay supplier
  const paySupplier = async () => {
    if (!selectedSupplier || !paymentAmount) {
      alert('الرجاء اختيار المورد وإدخال المبلغ');
      return;
    }

    try {
      await axios.post(`${API}/supplier-payment?supplier_id=${selectedSupplier}&amount=${paymentAmount}&payment_method=${paymentMethod}`);
      fetchSuppliers();
      fetchSupplierTransactions();
      setSelectedSupplier('');
      setPaymentAmount('');
      alert('تم دفع المبلغ للمورد بنجاح');
    } catch (error) {
      console.error('Error paying supplier:', error);
      alert('حدث خطأ في دفع المبلغ');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">الموردين</h1>
        <div className="flex space-x-4 space-x-reverse">
          <button
            onClick={() => setCurrentView('suppliers')}
            className={`px-4 py-2 rounded ${currentView === 'suppliers' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            الموردين
          </button>
          <button
            onClick={() => setCurrentView('products')}
            className={`px-4 py-2 rounded ${currentView === 'products' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            المنتجات
          </button>
          <button
            onClick={() => setCurrentView('transactions')}
            className={`px-4 py-2 rounded ${currentView === 'transactions' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            المعاملات
          </button>
          <button
            onClick={() => setCurrentView('payments')}
            className={`px-4 py-2 rounded ${currentView === 'payments' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            سداد الموردين
          </button>
        </div>
      </div>

      {/* Suppliers View */}
      {currentView === 'suppliers' && (
        <div>
          {/* Add New Supplier */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-lg font-semibold mb-4">إضافة مورد جديد</h3>
            <div className="grid grid-cols-3 gap-4">
              <input
                type="text"
                value={newSupplier.name}
                onChange={(e) => setNewSupplier({ ...newSupplier, name: e.target.value })}
                placeholder="اسم المورد"
                className="p-2 border border-gray-300 rounded"
              />
              <input
                type="text"
                value={newSupplier.phone}
                onChange={(e) => setNewSupplier({ ...newSupplier, phone: e.target.value })}
                placeholder="رقم الهاتف (اختياري)"
                className="p-2 border border-gray-300 rounded"
              />
              <input
                type="text"
                value={newSupplier.address}
                onChange={(e) => setNewSupplier({ ...newSupplier, address: e.target.value })}
                placeholder="العنوان (اختياري)"
                className="p-2 border border-gray-300 rounded"
              />
            </div>
            <button
              onClick={addSupplier}
              className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              إضافة المورد
            </button>
          </div>

          {/* Suppliers List */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">قائمة الموردين</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 p-2">اسم المورد</th>
                    <th className="border border-gray-300 p-2">الهاتف</th>
                    <th className="border border-gray-300 p-2">العنوان</th>
                    <th className="border border-gray-300 p-2">إجمالي المشتريات</th>
                    <th className="border border-gray-300 p-2">إجمالي المدفوع</th>
                    <th className="border border-gray-300 p-2">الرصيد المستحق</th>
                    <th className="border border-gray-300 p-2">إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers.map(supplier => (
                    <tr key={supplier.id}>
                      <td className="border border-gray-300 p-2 font-semibold">{supplier.name}</td>
                      <td className="border border-gray-300 p-2">{supplier.phone || '-'}</td>
                      <td className="border border-gray-300 p-2">{supplier.address || '-'}</td>
                      <td className="border border-gray-300 p-2">{currency} {(supplier.total_purchases || 0).toFixed(2)}</td>
                      <td className="border border-gray-300 p-2">{currency} {(supplier.total_paid || 0).toFixed(2)}</td>
                      <td className={`border border-gray-300 p-2 font-semibold ${(supplier.balance || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {currency} {(supplier.balance || 0).toFixed(2)}
                      </td>
                      <td className="border border-gray-300 p-2">
                        <div className="flex space-x-2 space-x-reverse">
                          <button
                            onClick={() => editSupplier(supplier)}
                            className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                            title="تحرير"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => deleteSupplier(supplier.id)}
                            className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                            title="حذف"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Products View */}
      {currentView === 'products' && (
        <div>
          {/* Add New Product */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-lg font-semibold mb-4">إضافة منتج محلي جديد</h3>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                value={newProduct.name}
                onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                placeholder="اسم المنتج"
                className="p-2 border border-gray-300 rounded"
              />
              <select
                value={newProduct.supplier_id}
                onChange={(e) => setNewProduct({ ...newProduct, supplier_id: e.target.value })}
                className="p-2 border border-gray-300 rounded"
              >
                <option value="">اختر المورد</option>
                {suppliers.map(supplier => (
                  <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
                ))}
              </select>
              <input
                type="number"
                step="0.01"
                value={newProduct.purchase_price}
                onChange={(e) => setNewProduct({ ...newProduct, purchase_price: e.target.value })}
                placeholder="سعر الشراء"
                className="p-2 border border-gray-300 rounded"
              />
              <input
                type="number"
                step="0.01"
                value={newProduct.selling_price}
                onChange={(e) => setNewProduct({ ...newProduct, selling_price: e.target.value })}
                placeholder="سعر البيع"
                className="p-2 border border-gray-300 rounded"
              />
            </div>
            <button
              onClick={addLocalProduct}
              className="mt-4 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            >
              إضافة المنتج
            </button>
          </div>

          {/* Products List */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">قائمة المنتجات المحلية</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 p-2">اسم المنتج</th>
                    <th className="border border-gray-300 p-2">المورد</th>
                    <th className="border border-gray-300 p-2">سعر الشراء</th>
                    <th className="border border-gray-300 p-2">سعر البيع</th>
                    <th className="border border-gray-300 p-2">المخزون الحالي</th>
                    <th className="border border-gray-300 p-2">إجمالي المباع</th>
                    <th className="border border-gray-300 p-2">إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {localProducts.map(product => (
                    <tr key={product.id}>
                      <td className="border border-gray-300 p-2 font-semibold">{product.name}</td>
                      <td className="border border-gray-300 p-2">{product.supplier_name}</td>
                      <td className="border border-gray-300 p-2">{currency} {product.purchase_price.toFixed(2)}</td>
                      <td className="border border-gray-300 p-2">{currency} {product.selling_price.toFixed(2)}</td>
                      <td className="border border-gray-300 p-2">{product.current_stock || 0}</td>
                      <td className="border border-gray-300 p-2">{product.total_sold || 0}</td>
                      <td className="border border-gray-300 p-2">
                        <div className="flex space-x-2 space-x-reverse">
                          <button
                            onClick={() => editLocalProduct(product)}
                            className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                            title="تحرير"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => deleteLocalProduct(product.id)}
                            className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                            title="حذف"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Transactions View */}
      {currentView === 'transactions' && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">معاملات الموردين</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">التاريخ</th>
                  <th className="border border-gray-300 p-2">المورد</th>
                  <th className="border border-gray-300 p-2">نوع المعاملة</th>
                  <th className="border border-gray-300 p-2">المبلغ</th>
                  <th className="border border-gray-300 p-2">الوصف</th>
                  <th className="border border-gray-300 p-2">المنتج</th>
                  <th className="border border-gray-300 p-2">الكمية</th>
                  {user?.username === 'master' && (
                    <th className="border border-gray-300 p-2">إجراءات</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {supplierTransactions.map(transaction => (
                  <tr key={transaction.id}>
                    <td className="border border-gray-300 p-2">
                      {new Date(transaction.date).toLocaleDateString('ar-EG')}
                    </td>
                    <td className="border border-gray-300 p-2">{transaction.supplier_name}</td>
                    <td className="border border-gray-300 p-2">
                      <span className={`px-2 py-1 rounded text-sm ${transaction.transaction_type === 'purchase'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                        }`}>
                        {transaction.transaction_type === 'purchase' ? 'شراء' : 'دفع'}
                      </span>
                    </td>
                    <td className={`border border-gray-300 p-2 font-semibold ${transaction.transaction_type === 'purchase' ? 'text-red-600' : 'text-green-600'
                      }`}>
                      {currency} {transaction.amount.toFixed(2)}
                    </td>
                    <td className="border border-gray-300 p-2">{transaction.description}</td>
                    <td className="border border-gray-300 p-2">{transaction.product_name || '-'}</td>
                    <td className="border border-gray-300 p-2">{transaction.quantity || '-'}</td>
                    {user?.username === 'master' && (
                      <td className="border border-gray-300 p-2 text-center">
                        <button
                          onClick={() => deleteSupplierTransaction(transaction.id)}
                          className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                          title="حذف المعاملة"
                        >
                          🗑️
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Payments View */}
      {currentView === 'payments' && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">سداد حسابات الموردين</h3>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <select
              value={selectedSupplier}
              onChange={(e) => setSelectedSupplier(e.target.value)}
              className="p-2 border border-gray-300 rounded"
            >
              <option value="">اختر المورد</option>
              {suppliers.filter(s => (s.balance || 0) > 0).map(supplier => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name} - مستحق: {currency} {(supplier.balance || 0).toFixed(2)}
                </option>
              ))}
            </select>
            <input
              type="number"
              step="0.01"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
              placeholder="المبلغ المدفوع"
              className="p-2 border border-gray-300 rounded"
            />
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="p-2 border border-gray-300 rounded"
            >
              <option value="cash">نقدي</option>
              <option value="vodafone_elsawy">فودافون 010</option>
              <option value="vodafone_wael">كاش 0100</option>
              <option value="instapay">انستا باي</option>
            </select>
          </div>
          <button
            onClick={paySupplier}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            دفع المبلغ
          </button>
        </div>
      )}
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';

  // Only Elsawy and Faster can access dashboard
  if (user?.username !== 'Elsawy' && user?.username !== 'Faster') {
    return (
      <div className="p-6" dir="rtl">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>غير مسموح!</strong> لوحة التحكم مخصصة للمدير فقط.
        </div>
      </div>
    );
  }

  const [stats, setStats] = useState({
    total_sales: 0,
    total_expenses: 0,
    net_profit: 0,
    total_unpaid: 0,
    invoice_count: 0,
    customer_count: 0
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const clearAllData = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع البيانات؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    try {
      // Clear all data from backend
      await axios.delete(`${API}/customers/clear-all`);
      await axios.delete(`${API}/raw-materials/clear-all`);
      await axios.delete(`${API}/finished-products/clear-all`);
      await axios.delete(`${API}/invoices/clear-all`);
      await axios.delete(`${API}/expenses/clear-all`);
      await axios.delete(`${API}/payments/clear-all`);
      await axios.delete(`${API}/work-orders/clear-all`);

      // Refresh dashboard stats
      fetchStats();

      alert('تم حذف جميع البيانات');
    } catch (error) {
      console.error('Error clearing all data:', error);
      alert('حدث خطأ في حذف البيانات');
    }
  };

  const printReport = (reportType) => {
    const currentDate = new Date().toLocaleDateString('ar-EG');
    let printContent = `
      <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1>ماستر سيل</h1>
          <p>الحرفيان شارع السوبر جيت - 01020630677</p>
          <h2>تقرير لوحة التحكم</h2>
          <p>التاريخ: ${currentDate}</p>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>إجمالي المبيعات:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${currency} ${stats.total_sales.toFixed(2)}</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>إجمالي المصروفات:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${currency} ${stats.total_expenses.toFixed(2)}</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>صافي الربح:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${currency} ${stats.net_profit.toFixed(2)}</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>المبالغ المستحقة:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${currency} ${stats.total_unpaid.toFixed(2)}</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>عدد الفواتير:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${stats.invoice_count}</td>
          </tr>
          <tr>
            <td style="border: 1px solid #ddd; padding: 10px;"><strong>عدد العملاء:</strong></td>
            <td style="border: 1px solid #ddd; padding: 10px;">${stats.customer_count}</td>
          </tr>
        </table>
      </div>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  };

  return (
    <div className="space-y-6" dir="rtl">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl p-6 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">لوحة التحكم</h2>
            <p className="text-blue-100">مرحباً {user?.username} - إليك نظرة عامة على أداء النشاط</p>
          </div>
          <div className="text-6xl opacity-20">📊</div>
        </div>

        <div className="flex flex-wrap space-x-4 space-x-reverse mt-6">
          <button
            onClick={clearAllData}
            className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl hover:transform hover:scale-105">
            🗑️ حذف الكل
          </button>
          <button
            onClick={fetchStats}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl hover:transform hover:scale-105">
            🔄 إعادة تحميل
          </button>
          <button
            onClick={() => printReport('dashboard')}
            className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl hover:transform hover:scale-105">
            🖨️ طباعة تقرير
          </button>
          <select className="bg-white text-gray-700 border-0 rounded-lg px-4 py-3 shadow-lg focus:ring-2 focus:ring-blue-300 font-medium">
            <option>📅 يومي</option>
            <option>📆 أسبوعي</option>
            <option>📊 شهري</option>
            <option>📈 سنوي</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Total Sales */}
        <div className="bg-gradient-to-br from-green-400 to-green-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">إجمالي المبيعات</h3>
              <p className="text-3xl font-bold mt-2">
                {currency} {stats.total_sales.toFixed(2)}
              </p>
            </div>
            <div className="text-5xl opacity-30">💰</div>
          </div>
        </div>

        {/* Total Expenses */}
        <div className="bg-gradient-to-br from-red-400 to-red-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">إجمالي المصروفات</h3>
              <p className="text-3xl font-bold mt-2">
                {currency} {stats.total_expenses.toFixed(2)}
              </p>
            </div>
            <div className="text-5xl opacity-30">💸</div>
          </div>
        </div>

        {/* Net Profit */}
        <div className="bg-gradient-to-br from-blue-400 to-blue-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">صافي الربح</h3>
              <p className="text-3xl font-bold mt-2">
                {currency} {stats.net_profit.toFixed(2)}
              </p>
            </div>
            <div className="text-5xl opacity-30">📈</div>
          </div>
        </div>

        {/* Unpaid Amount */}
        <div className="bg-gradient-to-br from-orange-400 to-orange-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">المبالغ المستحقة</h3>
              <p className="text-3xl font-bold mt-2">
                {currency} {stats.total_unpaid.toFixed(2)}
              </p>
            </div>
            <div className="text-5xl opacity-30">⏳</div>
          </div>
        </div>

        {/* Invoice Count */}
        <div className="bg-gradient-to-br from-purple-400 to-purple-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">عدد الفواتير</h3>
              <p className="text-3xl font-bold mt-2">
                {stats.invoice_count}
              </p>
            </div>
            <div className="text-5xl opacity-30">🧾</div>
          </div>
        </div>

        {/* Customer Count */}
        <div className="bg-gradient-to-br from-teal-400 to-teal-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:transform hover:scale-105">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold opacity-90">عدد العملاء</h3>
              <p className="text-3xl font-bold mt-2">
                {stats.customer_count}
              </p>
            </div>
            <div className="text-5xl opacity-30">👥</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Daily Sales Report Component - كشف المبيعات اليومي
const DailySalesReport = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [reportData, setReportData] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);

  const fetchReport = async (date) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/daily-sales-report`, {
        params: { report_date: date }
      });
      setReportData(response.data);
    } catch (error) {
      console.error('Error fetching daily sales report:', error);
      alert('حدث خطأ في جلب التقرير');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport(selectedDate);
  }, [selectedDate]);

  const handlePrint = () => {
    const printContent = document.getElementById('daily-report-content');
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(`
      <html dir="rtl">
        <head>
          <title>كشف مبيعات يومي - ${reportData?.report_date_formatted}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; direction: rtl; }
            .report-header { text-align: center; margin-bottom: 30px; }
            .report-title { font-size: 24px; font-weight: bold; color: #1e3a5f; }
            .report-date { font-size: 18px; color: #666; margin-top: 10px; }
            .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
            .card { border: 2px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; }
            .card-title { font-size: 14px; color: #555; margin-bottom: 10px; }
            .card-value { font-size: 24px; font-weight: bold; }
            .yellow { background: #fef3c7; border-color: #f59e0b; }
            .orange { background: #ffedd5; border-color: #f97316; }
            .green { background: #d1fae5; border-color: #10b981; }
            .pink { background: #fce7f3; border-color: #ec4899; }
            .blue { background: #dbeafe; border-color: #3b82f6; }
            .gray { background: #f3f4f6; border-color: #6b7280; }
            .accounts-section { margin-top: 30px; }
            .accounts-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
            @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
  };

  const formatNumber = (num) => {
    return (num || 0).toLocaleString('ar-EG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="p-4" dir="rtl">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-blue-800">📊 كشف المبيعات اليومي</h1>
        <div className="flex gap-3 items-center">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="p-2 border rounded-lg"
          />
          <button
            onClick={() => fetchReport(selectedDate)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            🔄 تحديث
          </button>
          <button
            onClick={handlePrint}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            🖨️ طباعة
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">جاري تحميل التقرير...</p>
        </div>
      ) : reportData ? (
        <div id="daily-report-content">
          {/* Report Header */}
          <div className="report-header text-center mb-8 bg-gradient-to-r from-blue-600 to-blue-800 text-white py-6 rounded-xl">
            <h2 className="report-title text-3xl font-bold">كشف مبيعات يومي</h2>
            <p className="report-date text-xl mt-2">📅 {reportData.report_date_formatted}</p>
          </div>

          {/* Main Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* مبيعات اليوم */}
            <div className="bg-yellow-100 border-2 border-yellow-500 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-yellow-800 mb-2">📊 مبيعات اليوم</h3>
              <p className="text-3xl font-bold text-yellow-700">
                {formatNumber(reportData.summary.total_sales)} {currency}
              </p>
              <p className="text-sm text-yellow-600 mt-2">
                {reportData.details.invoices_count} فاتورة
              </p>
            </div>

            {/* نقدي */}
            <div className="bg-orange-100 border-2 border-orange-500 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-orange-800 mb-2">💵 نقدي</h3>
              <p className="text-3xl font-bold text-orange-700">
                {formatNumber(reportData.summary.cash_sales)} {currency}
              </p>
            </div>

            {/* فودافون */}
            <div className="bg-red-100 border-2 border-red-500 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-red-800 mb-2">📱 فودافون</h3>
              <p className="text-3xl font-bold text-red-700">
                {formatNumber(reportData.summary.vodafone_sales)} {currency}
              </p>
            </div>

            {/* انستاباي */}
            <div className="bg-purple-100 border-2 border-purple-500 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-purple-800 mb-2">💳 انستاباي</h3>
              <p className="text-3xl font-bold text-purple-700">
                {formatNumber(reportData.summary.instapay_sales)} {currency}
              </p>
            </div>
          </div>

          {/* Second Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {/* آجل */}
            <div className="bg-emerald-100 border-2 border-emerald-600 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-emerald-800 mb-2">📝 آجل</h3>
              <p className="text-3xl font-bold text-emerald-700">
                {formatNumber(reportData.summary.deferred_sales)} {currency}
              </p>
              <p className="text-sm text-emerald-600 mt-2">فواتير آجل غير مدفوعة</p>
            </div>

            {/* تحصيل من الآجل */}
            <div className="bg-pink-100 border-2 border-pink-500 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-pink-800 mb-2">💰 تحصيل من الآجل</h3>
              <p className="text-3xl font-bold text-pink-700">
                {formatNumber(reportData.summary.deferred_collections)} {currency}
              </p>
              <p className="text-sm text-pink-600 mt-2">فواتير سابقة محصلة اليوم</p>
            </div>

            {/* مصروفات */}
            <div className="bg-gray-100 border-2 border-gray-400 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">📤 مصروفات</h3>
              <p className="text-3xl font-bold text-gray-700">
                {formatNumber(reportData.summary.total_expenses)} {currency}
              </p>
              <p className="text-sm text-gray-600 mt-2">{reportData.details.expenses_count} مصروف</p>
            </div>

            {/* صافي الدخل */}
            <div className="bg-gradient-to-r from-green-400 to-green-600 border-2 border-green-600 rounded-xl p-6 text-center shadow-lg">
              <h3 className="text-lg font-semibold text-white mb-2">✨ صافي الدخل اليومي</h3>
              <p className="text-3xl font-bold text-white">
                {formatNumber(reportData.summary.net_daily_income)} {currency}
              </p>
              <p className="text-sm text-green-100 mt-2">نقدي + فودافون + انستا + تحصيل</p>
            </div>
          </div>

          {/* Daily Account Changes */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">
              📈 الزيادة اليومية في الحسابات
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {reportData.daily_account_changes.map((account, index) => (
                <div
                  key={index}
                  className={`rounded-xl p-4 text-center ${account.daily_change >= 0
                    ? 'bg-green-50 border-2 border-green-300'
                    : 'bg-red-50 border-2 border-red-300'
                    }`}
                >
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">{account.label}</h4>
                  <p className={`text-xl font-bold ${account.daily_change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                    {account.daily_change >= 0 ? '+' : ''}{formatNumber(account.daily_change)} {currency}
                  </p>
                </div>
              ))}
            </div>
          </div>


        </div>
      ) : (
        <div className="text-center py-10 text-gray-500">
          لا توجد بيانات للعرض
        </div>
      )}
    </div>
  );
};

// Sales Component
const Sales = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [customers, setCustomers] = useState([]);
  const [newCustomer, setNewCustomer] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [suppliers, setSuppliers] = useState([]); // قائمة الموردين
  const [supervisorName, setSupervisorName] = useState(''); // اسم المشرف على التصنيع
  const [invoiceTitle, setInvoiceTitle] = useState(''); // عنوان الفاتورة
  const [currentItem, setCurrentItem] = useState({
    seal_type: 'RSL',
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    height: '',
    quantity: 1,
    unit_price: '',
    product_type: 'manufactured' // manufactured أو local
  });
  // New state for dual measurement inputs
  const [measurements, setMeasurements] = useState({
    inner_diameter_mm: '',
    inner_diameter_inch: '',
    outer_diameter_mm: '',
    outer_diameter_inch: '',
    height_mm: '',
    height_inch: '',
    wall_height_mm: '',
    wall_height_inch: ''
  });
  const [localProduct, setLocalProduct] = useState({
    product_size: '',      // مقاس المنتج
    product_type: '',      // نوع المنتج
    purchase_price: '',
    selling_price: '',
    supplier: ''
  });
  const [items, setItems] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState('نقدي');
  const [discount, setDiscount] = useState(0); // الخصم
  const [discountType, setDiscountType] = useState('amount'); // نوع الخصم: amount أو percentage
  const [compatibilityResults, setCompatibilityResults] = useState(null);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [selectedMaterials, setSelectedMaterials] = useState([]); // خامات متعددة مختارة
  const [measurementUnit, setMeasurementUnit] = useState('مم'); // بوصة أو مم
  const [wallHeight, setWallHeight] = useState(''); // ارتفاع الحيطة للـ W types
  const [clientType, setClientType] = useState(1); // نوع العميل للتسعير (1, 2, 3)

  // Measurement conversion functions
  const mmToInch = (mm) => {
    if (!mm || mm === '') return '';
    return (parseFloat(mm) / 25.4).toFixed(4);
  };

  const inchToMm = (inch) => {
    if (!inch || inch === '') return '';
    return (parseFloat(inch) * 25.4).toFixed(2);
  };

  // Handle measurement input changes with auto-conversion
  const handleMeasurementChange = (field, value, unit) => {
    const newMeasurements = { ...measurements };

    if (unit === 'mm') {
      newMeasurements[`${field}_mm`] = value;
      newMeasurements[`${field}_inch`] = mmToInch(value);
    } else {
      newMeasurements[`${field}_inch`] = value;
      newMeasurements[`${field}_mm`] = inchToMm(value);
    }

    setMeasurements(newMeasurements);

    // Update currentItem with mm values (for backend compatibility)
    const mmValue = parseFloat(newMeasurements[`${field}_mm`]) || '';
    setCurrentItem({
      ...currentItem,
      [field]: mmValue
    });
  };

  const sealTypes = ['RSL', 'RS', 'RSS', 'RSE', 'B17', 'B3', 'B14', 'B1', 'R15', 'R17', 'W1', 'W4', 'W5', 'W11', 'WBT', 'XR', 'CH', 'VR'];
  const materialTypes = ['NBR', 'BUR', 'BT', 'VT', 'BOOM'];

  useEffect(() => {
    fetchCustomers();
    fetchSuppliers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      // Sort customers alphabetically by name
      const sortedCustomers = (response.data || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'ar')
      );
      setCustomers(sortedCustomers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/suppliers`);
      setSuppliers(response.data || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    }
  };

  // Calculate automatic pricing based on material and client type
  const calculateAutomaticPrice = async (material, height, clientType) => {
    try {
      const response = await axios.post(`${API}/calculate-price`, null, {
        params: {
          material_type: material.material_type,
          inner_diameter: material.inner_diameter,
          outer_diameter: material.outer_diameter,
          height: height,
          client_type: clientType
        }
      });

      return response.data;
    } catch (error) {
      console.log('No pricing found for this material combination:', error);
      return null;
    }
  };

  // Confirm multi-material selection and calculate pricing
  const confirmMultiMaterialSelection = async () => {
    try {
      // Calculate total pricing for all selected materials
      let totalPrice = 0;
      const height = parseFloat(currentItem.height);

      for (const selected of selectedMaterials) {
        const pricing = await calculateAutomaticPrice(selected.material, height, clientType);
        if (pricing) {
          totalPrice += pricing.total_price * selected.seals;
        }
      }

      // Update the current item with the calculated price
      setCurrentItem({
        ...currentItem,
        unit_price: (totalPrice / parseInt(currentItem.quantity)).toFixed(2)
      });

      // Set the first material as the selected material for compatibility
      if (selectedMaterials.length > 0) {
        setSelectedMaterial(selectedMaterials[0].material);
      }

      alert(`✅ تم تأكيد اختيار الخامات بنجاح!

📊 ملخص الاختيار:
${selectedMaterials.map(sel => `- ${sel.material.unit_code}: ${sel.seals} سيل`).join('\n')}

💰 السعر الإجمالي: ${totalPrice.toFixed(2)} ${currency}
💰 سعر السيل الواحد: ${(totalPrice / parseInt(currentItem.quantity)).toFixed(2)} ${currency}`);

    } catch (error) {
      console.error('Error confirming multi-material selection:', error);
      alert('حدث خطأ في تأكيد الاختيار');
    }
  };

  const checkCompatibility = async () => {
    if (!currentItem.inner_diameter || !currentItem.outer_diameter || !currentItem.height) {
      alert('الرجاء إدخال جميع المقاسات المطلوبة');
      return;
    }

    let innerDiameter = parseFloat(currentItem.inner_diameter);
    let outerDiameter = parseFloat(currentItem.outer_diameter);
    let height = parseFloat(currentItem.height);

    if (isNaN(innerDiameter) || isNaN(outerDiameter) || isNaN(height)) {
      alert('الرجاء إدخال أرقام صحيحة للمقاسات');
      return;
    }

    // Convert from inches to millimeters if needed
    if (measurementUnit === 'بوصة') {
      innerDiameter = innerDiameter * 25.4;
      outerDiameter = outerDiameter * 25.4;
      height = height * 25.4;

      console.log(`تحويل من بوصة إلى ملليمتر:
        القطر الداخلي: ${currentItem.inner_diameter} بوصة = ${innerDiameter.toFixed(1)} مم
        القطر الخارجي: ${currentItem.outer_diameter} بوصة = ${outerDiameter.toFixed(1)} مم
        الارتفاع: ${currentItem.height} بوصة = ${height.toFixed(1)} مم`);
    }

    try {
      const response = await axios.post(`${API}/compatibility-check`, {
        seal_type: currentItem.seal_type,
        material_type: currentItem.material_type,
        inner_diameter: innerDiameter,
        outer_diameter: outerDiameter,
        height: height
      });
      setCompatibilityResults(response.data);
    } catch (error) {
      console.error('Error checking compatibility:', error);
      alert('حدث خطأ في فحص التوافق');
    }
  };

  const addItem = () => {
    if (currentItem.product_type === 'manufactured') {
      // Validation for manufactured products - check if at least one measurement is filled
      const hasInnerDiameter = measurements.inner_diameter_mm || measurements.inner_diameter_inch;
      const hasOuterDiameter = measurements.outer_diameter_mm || measurements.outer_diameter_inch;
      const hasHeight = measurements.height_mm || measurements.height_inch;

      if (!hasInnerDiameter || !hasOuterDiameter || !hasHeight || !currentItem.unit_price) {
        alert('الرجاء إدخال جميع البيانات المطلوبة (القياسات والسعر)');
        return;
      }

      // Use mm values (they're automatically kept in sync by handleMeasurementChange)
      const innerDiameter = parseFloat(currentItem.inner_diameter);
      const outerDiameter = parseFloat(currentItem.outer_diameter);
      const height = parseFloat(currentItem.height);
      const wallHeightValue = parseFloat(measurements.wall_height_mm) || null;

      const item = {
        ...currentItem,
        inner_diameter: innerDiameter,
        outer_diameter: outerDiameter,
        height: height,
        quantity: parseInt(currentItem.quantity),
        unit_price: parseFloat(currentItem.unit_price),
        total_price: parseFloat(currentItem.unit_price) * parseInt(currentItem.quantity),
        wall_height: wallHeightValue,
        // Store original display values for both units
        display_measurements: {
          inner_diameter_mm: measurements.inner_diameter_mm,
          inner_diameter_inch: measurements.inner_diameter_inch,
          outer_diameter_mm: measurements.outer_diameter_mm,
          outer_diameter_inch: measurements.outer_diameter_inch,
          height_mm: measurements.height_mm,
          height_inch: measurements.height_inch,
          wall_height_mm: measurements.wall_height_mm,
          wall_height_inch: measurements.wall_height_inch
        },
        material_used: selectedMaterial ? selectedMaterial.unit_code : null,
        material_details: selectedMaterial ? {
          id: selectedMaterial.id,
          unit_code: selectedMaterial.unit_code,
          inner_diameter: selectedMaterial.inner_diameter,
          outer_diameter: selectedMaterial.outer_diameter,
          height: selectedMaterial.height,
          material_type: selectedMaterial.material_type,
          is_finished_product: selectedMaterial.is_finished_product || false
        } : {
          // إرسال معلومات المادة الأساسية حتى بدون اختيار مادة محددة
          material_type: currentItem.material_type,
          inner_diameter: parseFloat(currentItem.inner_diameter),
          outer_diameter: parseFloat(currentItem.outer_diameter),
          is_finished_product: false
        },
        // إضافة معلومات الخامات المتعددة
        selected_materials: selectedMaterials.length > 0 ? selectedMaterials.map(sel => ({
          unit_code: sel.material.unit_code,
          material_type: sel.material.material_type,
          inner_diameter: sel.material.inner_diameter,
          outer_diameter: sel.material.outer_diameter,
          height: sel.material.height,
          seals_count: sel.seals,
          id: sel.material.id
        })) : null
      };

      setItems([...items, item]);
      setCurrentItem({
        seal_type: 'RSL',
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        height: '',
        quantity: 1,
        unit_price: '',
        product_type: 'manufactured'
      });
      setMeasurements({
        inner_diameter_mm: '',
        inner_diameter_inch: '',
        outer_diameter_mm: '',
        outer_diameter_inch: '',
        height_mm: '',
        height_inch: '',
        wall_height_mm: '',
        wall_height_inch: ''
      });
    } else {
      // Validation for local products
      if (!localProduct.product_size || !localProduct.product_type || !localProduct.selling_price || !localProduct.supplier || !localProduct.purchase_price) {
        alert('الرجاء إدخال جميع بيانات المنتج المحلي');
        return;
      }

      const product_name = `${localProduct.product_size} - ${localProduct.product_type}`;

      const item = {
        // للمنتجات المحلية، حقول المنتجات المصنعة يجب أن تكون null
        seal_type: null,
        material_type: null,
        inner_diameter: null,
        outer_diameter: null,
        height: null,
        product_type: 'local',
        product_name: product_name,
        product_size: localProduct.product_size,
        product_type_name: localProduct.product_type,
        supplier: localProduct.supplier,
        purchase_price: parseFloat(localProduct.purchase_price),
        selling_price: parseFloat(localProduct.selling_price),
        quantity: parseInt(currentItem.quantity),
        unit_price: parseFloat(localProduct.selling_price), // Use selling price as unit price
        total_price: parseFloat(localProduct.selling_price) * parseInt(currentItem.quantity),
        // Store local product details
        local_product_details: {
          product_size: localProduct.product_size,
          product_type: localProduct.product_type,
          supplier: localProduct.supplier,
          purchase_price: parseFloat(localProduct.purchase_price),
          selling_price: parseFloat(localProduct.selling_price)
        }
      };

      setItems([...items, item]);
      setLocalProduct({
        product_size: '',
        product_type: '',
        purchase_price: '',
        selling_price: '',
        supplier: ''
      });
      setCurrentItem({
        seal_type: 'RSL',
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        height: '',
        quantity: 1,
        unit_price: '',
        product_type: 'manufactured'
      });
      setMeasurements({
        inner_diameter_mm: '',
        inner_diameter_inch: '',
        outer_diameter_mm: '',
        outer_diameter_inch: '',
        height_mm: '',
        height_inch: '',
        wall_height_mm: '',
        wall_height_inch: ''
      });
    }

    setCompatibilityResults(null);
    setSelectedMaterial(null);
    setSelectedMaterials([]); // مسح الخامات المختارة المتعددة
  };

  const editItem = (index) => {
    const item = items[index];

    // Set current item for editing
    setCurrentItem({
      seal_type: item.seal_type || 'RSL',
      material_type: item.material_type || 'NBR',
      inner_diameter: item.inner_diameter?.toString() || '',
      outer_diameter: item.outer_diameter?.toString() || '',
      height: item.height?.toString() || '',
      quantity: item.quantity || 1,
      unit_price: item.unit_price?.toString() || '',
      product_type: item.product_type || (item.local_product_details ? 'local' : 'manufactured')
    });

    // Set measurements for dual input fields (assuming values are in mm from database)
    setMeasurements({
      inner_diameter_mm: item.inner_diameter?.toString() || '',
      inner_diameter_inch: mmToInch(item.inner_diameter) || '',
      outer_diameter_mm: item.outer_diameter?.toString() || '',
      outer_diameter_inch: mmToInch(item.outer_diameter) || '',
      height_mm: item.height?.toString() || '',
      height_inch: mmToInch(item.height) || '',
      wall_height_mm: item.wall_height?.toString() || '',
      wall_height_inch: mmToInch(item.wall_height) || ''
    });

    // Set wall height if exists
    if (item.wall_height) {
      setWallHeight(item.wall_height.toString());
    }

    // Set measurement unit if exists
    if (item.measurement_unit) {
      setMeasurementUnit(item.measurement_unit);
    }

    // Set local product details if exists
    if (item.local_product_details) {
      setLocalProduct({
        product_size: item.local_product_details.product_size || '',
        product_type: item.local_product_details.product_type || '',
        purchase_price: '',
        selling_price: item.unit_price?.toString() || '',
        supplier: ''
      });
    }

    // Remove the item being edited
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  const deleteItem = (index) => {
    if (confirm('هل أنت متأكد من حذف هذا العنصر؟')) {
      const newItems = items.filter((_, i) => i !== index);
      setItems(newItems);
    }
  };

  const [isCreatingInvoice, setIsCreatingInvoice] = useState(false);

  const createInvoice = async () => {
    // منع التكرار أثناء إنشاء الفاتورة
    if (isCreatingInvoice) {
      return;
    }

    if (!selectedCustomer && !newCustomer) {
      alert('الرجاء اختيار العميل أو إدخال اسم عميل جديد');
      return;
    }

    if (items.length === 0) {
      alert('الرجاء إضافة منتجات للفاتورة');
      return;
    }

    try {
      setIsCreatingInvoice(true); // بدء إنشاء الفاتورة

      let customerId = selectedCustomer;
      let customerName = '';

      // إنشاء عميل جديد إذا لزم الأمر
      if (!selectedCustomer && newCustomer) {
        try {
          const customerResponse = await axios.post(`${API}/customers`, {
            name: newCustomer,
            phone: '',
            address: ''
          });
          customerId = customerResponse.data.id;
          customerName = newCustomer;

          // تحديث قائمة العملاء
          fetchCustomers();
        } catch (customerError) {
          // Check if it's a duplicate customer error
          if (customerError.response?.status === 409) {
            // Customer exists, ask user what to do
            const existingCustomer = customers.find(c => c.name.toLowerCase() === newCustomer.toLowerCase());
            if (existingCustomer) {
              if (confirm(`⚠️ العميل "${newCustomer}" موجود بالفعل!\n\nهل تريد استخدام العميل الموجود؟`)) {
                customerId = existingCustomer.id;
                customerName = existingCustomer.name;
                setSelectedCustomer(existingCustomer.id);
                setNewCustomer('');
              } else {
                setIsCreatingInvoice(false);
                return;
              }
            } else {
              alert(`❌ ${customerError.response.data.detail}\n\nيرجى اختيار العميل من القائمة.`);
              setIsCreatingInvoice(false);
              return;
            }
          } else {
            throw customerError;
          }
        }
      } else {
        const customer = customers.find(c => c.id === customerId);
        customerName = customer ? customer.name : '';
      }

      // حساب الإجمالي والخصم
      const subtotal = items.reduce((sum, item) => sum + item.total_price, 0);
      const discountAmount = discountType === 'percentage'
        ? (subtotal * parseFloat(discount || 0)) / 100
        : parseFloat(discount || 0);
      const totalAfterDiscount = subtotal - discountAmount;

      // إنشاء الفاتورة
      const invoiceData = {
        customer_id: customerId,
        customer_name: customerName,
        invoice_title: invoiceTitle, // عنوان الفاتورة
        supervisor_name: supervisorName, // اسم المشرف
        items: items,
        payment_method: paymentMethod,
        subtotal: subtotal,
        discount: discountAmount,
        discount_type: discountType,
        discount_value: parseFloat(discount || 0),
        total_after_discount: totalAfterDiscount,
        notes: ''
      };

      const response = await axios.post(`${API}/invoices?supervisor_name=${encodeURIComponent(supervisorName)}`, invoiceData);

      if (response.data) {
        // طباعة الفاتورة أولاً (قبل مسح البيانات وقبل أي alert لتجنب حظر النافذة المنبثقة)
        printInvoice(response.data);

        // مسح البيانات
        setItems([]);
        setSelectedCustomer('');
        setNewCustomer('');
        setSupervisorName('');
        setInvoiceTitle(''); // مسح عنوان الفاتورة
        setPaymentMethod('نقدي');
        setDiscount(0);
        setDiscountType('amount');
        setClientType(1); // إعادة تعيين نوع العميل
      }
    } catch (error) {
      console.error('Error creating invoice:', error);
      alert('حدث خطأ في إنشاء الفاتورة: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsCreatingInvoice(false); // إنهاء حالة الإنشاء
    }
  };

  const printInvoice = async (invoice) => {
    // Fetch company settings
    let s = {};
    try {
      const res = await axios.get(`${API}/settings`);
      s = res.data;
    } catch (e) { console.error('Settings fetch error:', e); }
    const cur = s.currency || 'ج.م';
    const lang = s.invoice_language || 'ar';
    const isEn = lang === 'en';
    const dir = isEn ? 'ltr' : 'rtl';
    const textAlign = isEn ? 'left' : 'right';
    // Use English fields when available for English invoice, fallback to Arabic
    const companyNameFull = isEn && s.company_name_full_en ? s.company_name_full_en : (s.company_name_full || 'شركة ماستر سيل');
    const companySubtitle = isEn && s.company_subtitle_en ? s.company_subtitle_en : (s.company_subtitle || 'تصنيع جميع أنواع الأويل سيل');
    const companyDetails1 = isEn && s.company_details_1_en ? s.company_details_1_en : (s.company_details_1 || 'جميع الأقطار حتى ٥٠٠مل');
    const companyDetails2 = isEn && s.company_details_2_en ? s.company_details_2_en : (s.company_details_2 || 'هيدروليك - نيوماتيك');
    const companyAddress = isEn && s.company_address_en ? s.company_address_en : (s.company_address || 'الحرفيين - السلام - أمام السوبر جيت');
    const companyMobile = isEn && s.company_mobile_en ? s.company_mobile_en : (s.company_mobile || '٠١٠٢٠٦٣٠٦٧٧ - ٠١٠٦٢٣٩٠٨٧٠');
    const companyLandline = isEn && s.company_landline_en ? s.company_landline_en : (s.company_landline || '٠١٠٢٠٦٣٠٦٧٧');
    const logoUrl = s.logo_url || 'https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg';

    const printContent = `
      <!DOCTYPE html>
      <html dir="${dir}">
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            direction: ${dir};
            font-size: 15px;
          }
          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
          }
          .company-info {
            text-align: ${textAlign};
          }
          .company-name {
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin: 0;
          }
          .company-subtitle {
            font-size: 20px;
            margin: 5px 0;
            color: #666;
          }
          .company-details {
            font-size: 16px;
            margin: 2px 0;
            color: #333;
          }
          .logo-section {
            text-align: center;
            flex: 1;
          }
          .invoice-title {
            font-size: 20px;
            font-weight: bold;
            background-color: #ff4444;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            display: inline-block;
            margin-bottom: 10px;
          }
          .invoice-number {
            font-size: 18px;
            font-weight: bold;
            color: #ff4444;
          }
          .customer-info {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
          }
          .customer-details {
            text-align: ${textAlign};
          }
          .date-info {
            text-align: ${isEn ? 'right' : 'left'};
          }
          .products-table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid #000;
            margin: 20px 0;
          }
          .products-table th,
          .products-table td {
            border: 1px solid #000;
            padding: 8px;
            text-align: center;
          }
          .products-table th {
            background-color: #f0f0f0;
            font-weight: bold;
          }
          .footer {
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 15px;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
          }
          .total-section {
            text-align: ${isEn ? 'right' : 'left'};
            margin-top: 10px;
          }
          .total-amount {
            font-size: 18px;
            font-weight: bold;
            border: 2px solid #000;
            padding: 10px;
            display: inline-block;
            background-color: #f9f9f9;
          }
          @media print {
            body { margin: 0; padding: 10px; }
          }
        </style>
      </head>
      <body>
        <!-- Header Section -->
        <div class="header">
          <div class="company-info">
            <h1 class="company-name">${companyNameFull}</h1>
            <p class="company-subtitle">${companySubtitle}</p>
            <p class="company-details">${companyDetails1}</p>
            <p class="company-details">${companyDetails2}</p>
          </div>
          
          <div class="logo-section">
            <img src="${logoUrl}" 
                 alt="Logo" 
                 style="max-width: 120px; max-height: 80px; margin-bottom: 10px;">
            <div class="invoice-title">${isEn ? (invoice.invoice_title === 'فاتورة' ? 'Invoice' : invoice.invoice_title === 'عرض سعر' ? 'Quotation' : invoice.invoice_title || 'Quotation') : (invoice.invoice_title || 'عرض سعر')}</div>
            <div class="invoice-number">${invoice.invoice_number}</div>
          </div>
        </div>

        <!-- Customer and Date Info -->
        <div class="customer-info">
          <div class="customer-details">
            <p><strong>${isEn ? 'To:' : 'السادة:'}</strong> ${invoice.customer_name}</p>
            <p><strong>${isEn ? 'Address:' : 'العنوان:'}</strong> ${invoice.customer_address || '........................'}</p>
          </div>
          <div class="date-info">
            <p><strong>${isEn ? 'Date:' : 'تحرير في:'}</strong> ${isEn ? new Date(invoice.date).toLocaleDateString('en-GB') : new Date(invoice.date).toLocaleDateString('ar-EG')}</p>
            ${isEn ? '' : `<p><strong>Date:</strong> ${new Date(invoice.date).toLocaleDateString('en-GB')}</p>`}
          </div>
        </div>

        <!-- Products Table -->
        <table class="products-table">
          <thead>
            <tr>
              <th style="width: 60px;">${isEn ? 'Item' : 'المسلسل<br>Item'}</th>
              <th style="width: 80px;">${isEn ? 'Qty' : 'الكمية<br>QTY'}</th>
              <th style="width: 200px;">${isEn ? 'Description' : 'Description<br>المواصفات'}</th>
              <th style="width: 100px;">${isEn ? 'Unit Price' : 'سعر الوحدة<br>Unit Price'}</th>
              <th style="width: 100px;">${isEn ? 'Total' : 'إجمالي<br>Total'}</th>
            </tr>
          </thead>
          <tbody>
            ${invoice.items.map((item, index) => `
              <tr>
                <td>${index + 1}</td>
                <td>${item.quantity}</td>
                <td style="text-align: ${textAlign};">
                  ${item.local_product_details ?
        `${item.local_product_details.product_size} - ${item.local_product_details.product_type}` :
        `${item.seal_type} - ${item.material_type}<br>
                    <small>${item.inner_diameter} × ${item.outer_diameter} × ${item.height} ${isEn ? 'mm' : 'مم'}${item.wall_height ? ` (${isEn ? 'wall height' : 'ارتفاع الحيطة'}: ${item.wall_height} ${isEn ? 'mm' : 'مم'})` : ""}</small>`
      }
                </td>
                <td>${cur} ${item.unit_price.toFixed(2)}</td>
                <td>${cur} ${item.total_price.toFixed(2)}</td>
              </tr>
            `).join('')}
            <!-- Empty rows for additional items -->
            ${Array.from({ length: Math.max(0, 8 - invoice.items.length) }, (_, i) => `
              <tr style="height: 40px;">
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <!-- Total Section -->
        <div class="total-section">
          <div style="text-align: ${isEn ? 'right' : 'left'}; margin-bottom: 10px;">
            ${invoice.subtotal ? `
              <div style="margin-bottom: 5px;">
                <span>${isEn ? 'Subtotal' : 'المجموع الفرعي'}: ${cur} ${invoice.subtotal.toFixed(2)}</span>
              </div>
            ` : ''}
            ${invoice.discount && invoice.discount > 0 ? `
              <div style="margin-bottom: 5px; color: #d32f2f;">
                <span>${isEn ? 'Discount' : 'الخصم'}: - ${cur} ${invoice.discount.toFixed(2)}</span>
                ${invoice.discount_type === 'percentage' && invoice.discount_value ?
          ` <small>(${invoice.discount_value}%)</small>` : ''}
              </div>
              <hr style="margin: 5px 0; border: 1px solid #000;">
            ` : ''}
          </div>
          <div class="total-amount">
            ${isEn ? 'Grand Total' : 'الإجمالي النهائي'}: ${cur} ${(invoice.total_after_discount || invoice.total_amount).toFixed(2)}
          </div>
        </div>

        <!-- Additional Info -->
        <div style="margin-top: 20px; text-align: center; font-size: 12px;">
          <p><strong>${isEn ? 'Note:' : 'ملحوظة:'}</strong> ${isEn ? 'Amount in words:' : 'فقط وقدره'}</p>
          <div style="height: 30px; border-bottom: 1px solid #000; margin: 10px 40px;"></div>
        </div>

        <!-- Footer -->
        <div class="footer">
          <div>
            <p><strong>${isEn ? 'Signature:' : 'التوقيع:'}</strong></p>
            <p>${isEn ? 'Mobile' : 'موبايل'}: ${companyMobile}</p>
            <p>${isEn ? 'Phone' : 'تليفون'}: ${companyLandline}</p>
          </div>
          <div style="text-align: ${isEn ? 'right' : 'left'};">
            <p><strong>${isEn ? 'Received by:' : 'المستلم:'}</strong></p>
            <p>${companyAddress}</p>
            <p>${isEn ? 'Mobile' : 'موبايل'}: ${companyMobile}</p>
          </div>
        </div>

        <!-- Note -->
        <div style="text-align: center; margin-top: 20px; font-size: 11px; color: #666;">
          <p>${isEn ? 'The buyer acknowledges that the goods have been inspected and accepted.' : 'يقر المشتري بأنه قام بمعاينة البضاعة وقبولها'}</p>
        </div>
      </body>
      </html>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  };

  const clearAllInvoices = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع العناصر؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    try {
      setItems([]);
      alert('تم حذف جميع العناصر');
    } catch (error) {
      alert('حدث خطأ في حذف البيانات');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <h2 className="text-2xl font-bold text-blue-600 mb-6">المبيعات</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Selection */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">اختيار العميل</h3>

          <div className="space-y-4">
            <div>
              <select
                value={selectedCustomer}
                onChange={(e) => setSelectedCustomer(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
              >
                <option value="">اختر العميل</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-2 space-x-reverse">
              <div className="flex-1">
                <input
                  type="text"
                  value={newCustomer}
                  onChange={(e) => {
                    const value = e.target.value;
                    setNewCustomer(value);

                    // Check for exact match and auto-select
                    const exactMatch = customers.find(c => c.name.toLowerCase() === value.toLowerCase());
                    if (exactMatch) {
                      // Auto-select the existing customer
                      setSelectedCustomer(exactMatch.id);
                      setNewCustomer('');
                      e.target.style.borderColor = '';
                      e.target.style.backgroundColor = '';
                      // Show brief confirmation
                      const tempMsg = document.createElement('div');
                      tempMsg.textContent = `✅ تم اختيار: ${exactMatch.name}`;
                      tempMsg.className = 'text-xs text-green-600 mt-1';
                      e.target.parentElement.appendChild(tempMsg);
                      setTimeout(() => tempMsg.remove(), 2000);
                    } else {
                      // Check for potential duplicates (partial match)
                      const partialMatch = customers.some(c => c.name.toLowerCase().includes(value.toLowerCase()) && value.length > 2);
                      if (partialMatch && value) {
                        e.target.style.borderColor = 'orange';
                        e.target.style.backgroundColor = '#fff3cd';
                      } else {
                        e.target.style.borderColor = '';
                        e.target.style.backgroundColor = '';
                      }
                    }
                  }}
                  placeholder="اسم عميل جديد"
                  className="w-full p-2 border border-gray-300 rounded"
                />
              </div>
              <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                عميل جديد
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">اسم المشرف على التصنيع</label>
              <input
                type="text"
                value={supervisorName}
                onChange={(e) => setSupervisorName(e.target.value)}
                placeholder="اسم المشرف (اختياري)"
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">عنوان الفاتورة</label>
              <input
                type="text"
                value={invoiceTitle}
                onChange={(e) => setInvoiceTitle(e.target.value)}
                placeholder="عنوان الفاتورة (اختياري)"
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
          </div>
        </div>

        {/* Product Entry */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">إضافة منتج</h3>

          {/* Product Type Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">نوع المنتج</label>
            <select
              value={currentItem.product_type}
              onChange={(e) => setCurrentItem({ ...currentItem, product_type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="manufactured">منتج تصنيع</option>
              <option value="local">منتج محلي</option>
            </select>
          </div>

          {/* Conditional Product Forms */}
          {currentItem.product_type === 'manufactured' ? (
            // Manufacturing Product Form
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">نوع السيل</label>
                  <select
                    value={currentItem.seal_type}
                    onChange={(e) => setCurrentItem({ ...currentItem, seal_type: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  >
                    {sealTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">نوع الخامة</label>
                  <select
                    value={currentItem.material_type}
                    onChange={(e) => setCurrentItem({ ...currentItem, material_type: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  >
                    {materialTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">القطر الداخلي</label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">مليمتر</label>
                      <input
                        type="number"
                        step="0.01"
                        value={measurements.inner_diameter_mm}
                        onChange={(e) => handleMeasurementChange('inner_diameter', e.target.value, 'mm')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="مم"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">بوصة</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={measurements.inner_diameter_inch}
                        onChange={(e) => handleMeasurementChange('inner_diameter', e.target.value, 'inch')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="بوصة"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">القطر الخارجي</label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">مليمتر</label>
                      <input
                        type="number"
                        step="0.01"
                        value={measurements.outer_diameter_mm}
                        onChange={(e) => handleMeasurementChange('outer_diameter', e.target.value, 'mm')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="مم"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">بوصة</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={measurements.outer_diameter_inch}
                        onChange={(e) => handleMeasurementChange('outer_diameter', e.target.value, 'inch')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="بوصة"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">ارتفاع السيل</label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">مليمتر</label>
                      <input
                        type="number"
                        step="0.01"
                        value={measurements.height_mm}
                        onChange={(e) => handleMeasurementChange('height', e.target.value, 'mm')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="مم"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">بوصة</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={measurements.height_inch}
                        onChange={(e) => handleMeasurementChange('height', e.target.value, 'inch')}
                        className="w-full p-2 border border-gray-300 rounded text-sm"
                        placeholder="بوصة"
                      />
                    </div>
                  </div>
                </div>

                {/* Wall Height for W-type seals */}
                {currentItem.seal_type && currentItem.seal_type.startsWith('W') && (
                  <div>
                    <label className="block text-sm font-medium mb-1">ارتفاع الحيطة</label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">مليمتر</label>
                        <input
                          type="number"
                          step="0.01"
                          value={measurements.wall_height_mm}
                          onChange={(e) => handleMeasurementChange('wall_height', e.target.value, 'mm')}
                          className="w-full p-2 border border-gray-300 rounded text-sm"
                          placeholder="ارتفاع الحيطة بالمليمتر"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">بوصة</label>
                        <input
                          type="number"
                          step="0.0001"
                          value={measurements.wall_height_inch}
                          onChange={(e) => handleMeasurementChange('wall_height', e.target.value, 'inch')}
                          className="w-full p-2 border border-gray-300 rounded text-sm"
                          placeholder="ارتفاع الحيطة بالبوصة"
                        />
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-1">عدد السيل</label>
                  <input
                    type="number"
                    value={currentItem.quantity}
                    onChange={(e) => setCurrentItem({ ...currentItem, quantity: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">نوع العميل للتسعير</label>
                  <select
                    value={clientType}
                    onChange={(e) => setClientType(parseInt(e.target.value))}
                    className="w-full p-2 border border-gray-300 rounded"
                  >
                    <option value={1}>عميل 1</option>
                    <option value={2}>عميل 2</option>
                    <option value={3}>عميل 3</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">سعر السيل الواحد</label>
                  <input
                    type="number"
                    step="0.01"
                    value={currentItem.unit_price}
                    onChange={(e) => setCurrentItem({ ...currentItem, unit_price: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">ملاحظات</label>
                  <textarea
                    value={currentItem.notes || ''}
                    onChange={(e) => setCurrentItem({ ...currentItem, notes: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                    rows="2"
                    placeholder="ملاحظات إضافية..."
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={checkCompatibility}
                    className="w-full bg-yellow-500 text-white p-2 rounded hover:bg-yellow-600"
                  >
                    فحص التوافق
                  </button>
                </div>
              </div>
            </>
          ) : (
            // Local Product Form
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">مقاس المنتج</label>
                  <input
                    type="text"
                    value={localProduct.product_size}
                    onChange={(e) => setLocalProduct({ ...localProduct, product_size: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="مقاس المنتج"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">نوع المنتج</label>
                  <input
                    type="text"
                    value={localProduct.product_type}
                    onChange={(e) => setLocalProduct({ ...localProduct, product_type: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="نوع المنتج"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">المورد</label>
                  <select
                    value={localProduct.supplier}
                    onChange={(e) => setLocalProduct({ ...localProduct, supplier: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  >
                    <option value="">اختر المورد</option>
                    {suppliers.map(supplier => (
                      <option key={supplier.id} value={supplier.name}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">سعر الشراء</label>
                  <input
                    type="number"
                    step="0.01"
                    value={localProduct.purchase_price}
                    onChange={(e) => setLocalProduct({ ...localProduct, purchase_price: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="سعر الشراء"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">سعر البيع</label>
                  <input
                    type="number"
                    step="0.01"
                    value={localProduct.selling_price}
                    onChange={(e) => setLocalProduct({ ...localProduct, selling_price: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="سعر البيع"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">الكمية</label>
                  <input
                    type="number"
                    value={currentItem.quantity}
                    onChange={(e) => setCurrentItem({ ...currentItem, quantity: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded"
                  />
                </div>
              </div>
            </>
          )}

          <button
            onClick={addItem}
            className="w-full bg-green-500 text-white p-2 rounded hover:bg-green-600 mt-4"
          >
            إضافة للفاتورة
          </button>
        </div>
      </div>

      {/* Compatibility Results */}
      {compatibilityResults && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">نتائج فحص التوافق</h3>

          {compatibilityResults.compatible_materials.length > 0 && (
            <div className="mb-4">
              <h4 className="font-medium mb-2">📦 نتائج فحص التوافق</h4>
              <p className="text-sm text-gray-600 mb-2">اختر الخامات وحدد عدد السيلات من كل خامة (المطلوب: {currentItem.quantity} سيل)</p>

              {/* عرض الخامات المختارة */}
              {selectedMaterials.length > 0 && (
                <div className="mb-4 p-3 bg-blue-50 rounded border">
                  <h5 className="font-medium text-blue-800 mb-2">الخامات المختارة:</h5>
                  <div className="space-y-2">
                    {selectedMaterials.map((selected, index) => (
                      <div key={index} className="flex items-center justify-between bg-white p-2 rounded border">
                        <span className="text-sm">
                          {selected.material.unit_code} - {selected.material.material_type}
                          {selected.material.inner_diameter}×{selected.material.outer_diameter}×{selected.material.height}
                        </span>
                        <div className="flex items-center space-x-2 space-x-reverse">
                          <input
                            type="number"
                            min="1"
                            max={Math.floor(selected.material.height / (parseFloat(currentItem.height) + 2))}
                            value={selected.seals}
                            onChange={(e) => {
                              const newSelected = [...selectedMaterials];
                              newSelected[index].seals = parseInt(e.target.value) || 0;
                              setSelectedMaterials(newSelected);
                            }}
                            className="w-16 p-1 border rounded text-center"
                          />
                          <span className="text-xs">سيل</span>
                          <button
                            onClick={() => {
                              const newSelected = selectedMaterials.filter((_, i) => i !== index);
                              setSelectedMaterials(newSelected);
                            }}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 text-sm">
                    <span className="font-medium">
                      المجموع: {selectedMaterials.reduce((sum, sel) => sum + sel.seals, 0)} / {currentItem.quantity} سيل
                    </span>
                    {selectedMaterials.reduce((sum, sel) => sum + sel.seals, 0) === parseInt(currentItem.quantity) && (
                      <span className="text-green-600 ml-2">✓ مكتمل</span>
                    )}
                  </div>
                </div>
              )}

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {compatibilityResults.compatible_materials.map((material, index) => {
                  const isSelected = selectedMaterials.some(sel =>
                    sel.material.unit_code === material.unit_code &&
                    sel.material.inner_diameter === material.inner_diameter &&
                    sel.material.outer_diameter === material.outer_diameter
                  );
                  const maxSeals = Math.floor(material.height / (parseFloat(currentItem.height) + 2));
                  const remainingSeals = parseInt(currentItem.quantity) - selectedMaterials.reduce((sum, sel) => sum + sel.seals, 0);

                  return (
                    <div key={index}
                      className={`p-3 rounded border transition-colors ${isSelected ? 'bg-blue-100 border-blue-300' : 'bg-gray-50 hover:bg-gray-100'
                        }`}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-medium text-blue-600">
                            {material.unit_code} - {material.material_type}
                          </p>
                          <p className="text-sm text-gray-600">
                            الأبعاد: {material.inner_diameter} × {material.outer_diameter} × {material.height} مم
                          </p>
                          <p className="text-xs text-green-600">
                            يمكن إنتاج: {maxSeals} سيل كحد أقصى
                          </p>
                          {material.score && (
                            <p className="text-xs text-gray-500">نسبة التوافق: {material.score}%</p>
                          )}
                        </div>
                        {!isSelected && remainingSeals > 0 && maxSeals > 0 && (
                          <button
                            onClick={() => {
                              const newSelection = {
                                material: material,
                                seals: Math.min(maxSeals, remainingSeals)
                              };
                              setSelectedMaterials([...selectedMaterials, newSelection]);
                            }}
                            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                          >
                            اختيار
                          </button>
                        )}
                        {isSelected && (
                          <div className="text-blue-600 text-sm font-medium">
                            ✓ مختارة
                          </div>
                        )}
                        {!isSelected && remainingSeals <= 0 && (
                          <div className="text-gray-400 text-sm">
                            مكتمل
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* زر تأكيد الاختيار */}
              {selectedMaterials.length > 0 && (
                <div className="mt-4 flex space-x-2 space-x-reverse">
                  <button
                    onClick={() => {
                      const totalSeals = selectedMaterials.reduce((sum, sel) => sum + sel.seals, 0);
                      if (totalSeals !== parseInt(currentItem.quantity)) {
                        alert(`⚠️ مجموع السيلات المختارة (${totalSeals}) لا يساوي العدد المطلوب (${currentItem.quantity})`);
                        return;
                      }

                      // تأكيد الاختيار وحساب السعر
                      confirmMultiMaterialSelection();
                    }}
                    className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    disabled={selectedMaterials.reduce((sum, sel) => sum + sel.seals, 0) !== parseInt(currentItem.quantity)}
                  >
                    تأكيد الاختيار
                  </button>
                  <button
                    onClick={() => {
                      setSelectedMaterials([]);
                    }}
                    className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                  >
                    إلغاء الاختيار
                  </button>
                </div>
              )}
            </div>
          )}

          {compatibilityResults.compatible_products.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">المنتجات الجاهزة:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {compatibilityResults.compatible_products.map((product, index) => (
                  <div
                    key={index}
                    className="p-3 border border-blue-300 bg-blue-50 rounded cursor-pointer hover:bg-blue-100"
                    onClick={() => setSelectedMaterial({
                      unit_code: `FINISHED-${product.id}`,
                      material_type: product.material_type,
                      seal_type: product.seal_type,
                      inner_diameter: product.inner_diameter,
                      outer_diameter: product.outer_diameter,
                      height: product.height,
                      is_finished_product: true
                    })}
                  >
                    <p><strong>النوع:</strong> {product.seal_type} - {product.material_type}</p>
                    <p><strong>المقاس:</strong> {product.inner_diameter} × {product.outer_diameter} × {product.height}</p>
                    <p><strong>الكمية:</strong> {product.quantity}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedMaterial && (
            <div className="mt-4 p-3 bg-blue-100 rounded">
              <p className="font-semibold text-blue-800">
                تم اختيار الخامة: {selectedMaterial.unit_code} ({selectedMaterial.material_type})
              </p>
            </div>
          )}
        </div>
      )}

      {/* Current Items */}
      {items.length > 0 && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">الفواتير الأخيرة</h3>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">نوع السيل</th>
                  <th className="border border-gray-300 p-2">نوع الخامة</th>
                  <th className="border border-gray-300 p-2">المقاس</th>
                  <th className="border border-gray-300 p-2">الكمية</th>
                  <th className="border border-gray-300 p-2">السعر</th>
                  <th className="border border-gray-300 p-2">المجموع</th>
                  <th className="border border-gray-300 p-2">إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr key={index}>
                    <td className="border border-gray-300 p-2">
                      {item.local_product_details ? item.local_product_details.product_type : item.seal_type}
                    </td>
                    <td className="border border-gray-300 p-2">
                      {item.local_product_details ? 'محلي' : item.material_type}
                    </td>
                    <td className="border border-gray-300 p-2">
                      {item.local_product_details ?
                        `${item.local_product_details.product_size} - ${item.local_product_details.product_type}` :
                        `${item.original_inner_diameter || item.inner_diameter} × ${item.original_outer_diameter || item.outer_diameter} × ${item.original_height || item.height}${item.original_wall_height ? ` (ارتفاع الحيطة: ${item.original_wall_height})` : (item.wall_height ? ` (ارتفاع الحيطة: ${item.wall_height})` : '')} ${item.measurement_unit || 'مم'}`
                      }
                    </td>
                    <td className="border border-gray-300 p-2">{item.quantity}</td>
                    <td className="border border-gray-300 p-2">{currency} {item.unit_price}</td>
                    <td className="border border-gray-300 p-2">{currency} {item.total_price}</td>
                    <td className="border border-gray-300 p-2">
                      <div className="flex space-x-2 space-x-reverse">
                        <button
                          onClick={() => editItem(index)}
                          className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                          title="تحرير"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => deleteItem(index)}
                          className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                          title="حذف"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex justify-between items-center">
            <div>
              <label className="block text-sm font-medium mb-1">طريقة الدفع</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="p-2 border border-gray-300 rounded"
              >
                <option value="نقدي">نقدي</option>
                <option value="آجل">آجل</option>
                <option value="فودافون 010">فودافون 010</option>
                <option value="كاش 0100">كاش 0100</option>
                <option value="انستاباي">انستاباي</option>
                <option value="يد الصاوي">يد الصاوي</option>
              </select>
            </div>

            {/* Discount Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium mb-1">نوع الخصم</label>
                <select
                  value={discountType}
                  onChange={(e) => setDiscountType(e.target.value)}
                  className="p-2 border border-gray-300 rounded w-full"
                >
                  <option value="amount">مبلغ ثابت</option>
                  <option value="percentage">نسبة مئوية</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  قيمة الخصم {discountType === 'percentage' ? '(%)' : `(${currency})`}
                </label>
                <input
                  type="number"
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  className="p-2 border border-gray-300 rounded w-full"
                  placeholder="0"
                  min="0"
                  step={discountType === 'percentage' ? '0.1' : '0.01'}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">مبلغ الخصم</label>
                <div className="p-2 bg-white border border-gray-300 rounded w-full">
                  {currency} {(() => {
                    const subtotal = items.reduce((sum, item) => sum + item.total_price, 0);
                    const discountAmount = discountType === 'percentage'
                      ? (subtotal * parseFloat(discount || 0)) / 100
                      : parseFloat(discount || 0);
                    return discountAmount.toFixed(2);
                  })()}
                </div>
              </div>
            </div>

            {/* Total Section */}
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-lg">المجموع الفرعي:</span>
                <span className="text-lg font-semibold">
                  {currency} {items.reduce((sum, item) => sum + item.total_price, 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-lg">الخصم:</span>
                <span className="text-lg font-semibold text-red-600">
                  - {currency} {(() => {
                    const subtotal = items.reduce((sum, item) => sum + item.total_price, 0);
                    const discountAmount = discountType === 'percentage'
                      ? (subtotal * parseFloat(discount || 0)) / 100
                      : parseFloat(discount || 0);
                    return discountAmount.toFixed(2);
                  })()}
                </span>
              </div>
              <hr className="my-2" />
              <div className="flex justify-between items-center">
                <span className="text-xl font-bold">الإجمالي النهائي:</span>
                <span className="text-xl font-bold text-green-600">
                  {currency} {(() => {
                    const subtotal = items.reduce((sum, item) => sum + item.total_price, 0);
                    const discountAmount = discountType === 'percentage'
                      ? (subtotal * parseFloat(discount || 0)) / 100
                      : parseFloat(discount || 0);
                    return (subtotal - discountAmount).toFixed(2);
                  })()}
                </span>
              </div>
            </div>

            <div className="text-xl font-bold" style={{ display: 'none' }}>
              الإجمالي: {currency} {items.reduce((sum, item) => sum + item.total_price, 0).toFixed(2)}
            </div>
          </div>

          <button
            onClick={createInvoice}
            disabled={isCreatingInvoice}
            className={`w-full p-3 rounded mt-4 text-lg font-semibold ${isCreatingInvoice
              ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
              : 'bg-green-500 text-white hover:bg-green-600'
              }`}
          >
            {isCreatingInvoice ? 'جاري إنشاء الفاتورة...' : 'إنشاء الفاتورة'}
          </button>
        </div>
      )}
    </div>
  );
};

// Simple placeholder components for other pages
// Inventory Component will be replaced with new advanced version above

// Stock Component (Old Inventory functionality for Raw Materials and Finished Products)
const Stock = () => {
  const [rawMaterials, setRawMaterials] = useState([]);
  const [finishedProducts, setFinishedProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState(''); // للبحث
  const [newRawMaterial, setNewRawMaterial] = useState({
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    height: '',
    pieces_count: '',
    cost_per_mm: ''
  });
  const [newFinishedProduct, setNewFinishedProduct] = useState({
    seal_type: 'RSL',
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    height: '',
    quantity: '',
    unit_price: ''
  });

  const materialTypes = ['NBR', 'BUR', 'BT', 'VT', 'BOOM'];
  const sealTypes = ['RSL', 'RS', 'RSS', 'RSE', 'B17', 'B3', 'B14', 'B1', 'R15', 'R17', 'W1', 'W4', 'W5', 'W11', 'WBT', 'XR', 'CH', 'VR'];

  // دالة تصفية البحث
  const filteredRawMaterials = rawMaterials.filter(material =>
    material.material_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    material.unit_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    material.inner_diameter.toString().includes(searchTerm) ||
    material.outer_diameter.toString().includes(searchTerm) ||
    material.height.toString().includes(searchTerm)
  ).sort((a, b) => {
    // ترتيب حسب أولوية الخامة: BUR-NBR-BT-BOOM-VT
    const materialPriority = { 'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5 };
    const aPriority = materialPriority[a.material_type] || 6;
    const bPriority = materialPriority[b.material_type] || 6;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }
    // ثم ترتيب حسب المقاس (القطر الداخلي ثم الخارجي)
    if (a.inner_diameter !== b.inner_diameter) {
      return a.inner_diameter - b.inner_diameter;
    }
    return a.outer_diameter - b.outer_diameter;
  });

  const filteredFinishedProducts = finishedProducts.filter(product =>
    product.seal_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.material_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.inner_diameter.toString().includes(searchTerm) ||
    product.outer_diameter.toString().includes(searchTerm) ||
    product.height.toString().includes(searchTerm)
  ).sort((a, b) => {
    // ترتيب حسب أولوية الخامة: BUR-NBR-BT-BOOM-VT
    const materialPriority = { 'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5 };
    const aPriority = materialPriority[a.material_type] || 6;
    const bPriority = materialPriority[b.material_type] || 6;

    if (aPriority !== bPriority) {
      return aPriority - bPriority;
    }
    // ثم ترتيب حسب المقاس (القطر الداخلي ثم الخارجي)
    if (a.inner_diameter !== b.inner_diameter) {
      return a.inner_diameter - b.inner_diameter;
    }
    return a.outer_diameter - b.outer_diameter;
  });

  useEffect(() => {
    fetchRawMaterials();
    fetchFinishedProducts();
  }, []);

  const fetchRawMaterials = async () => {
    try {
      const response = await axios.get(`${API}/raw-materials`);
      setRawMaterials(response.data);
    } catch (error) {
      console.error('Error fetching raw materials:', error);
    }
  };

  const fetchFinishedProducts = async () => {
    try {
      const response = await axios.get(`${API}/finished-products`);
      setFinishedProducts(response.data);
    } catch (error) {
      console.error('Error fetching finished products:', error);
    }
  };

  const addRawMaterial = async () => {
    if (!newRawMaterial.inner_diameter || !newRawMaterial.outer_diameter || !newRawMaterial.height || !newRawMaterial.pieces_count || !newRawMaterial.cost_per_mm) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      const rawMaterial = {
        material_type: newRawMaterial.material_type,
        inner_diameter: parseFloat(newRawMaterial.inner_diameter),
        outer_diameter: parseFloat(newRawMaterial.outer_diameter),
        height: parseFloat(newRawMaterial.height),
        pieces_count: parseInt(newRawMaterial.pieces_count),
        cost_per_mm: parseFloat(newRawMaterial.cost_per_mm)
        // unit_code will be generated automatically by backend
      };

      let response;
      if (newRawMaterial.id) {
        // Update existing material
        response = await axios.put(`${API}/raw-materials/${newRawMaterial.id}`, rawMaterial);
        alert(`تم تحديث المادة الخام بنجاح. كود الوحدة: ${response.data.unit_code}`);
      } else {
        // Add new material
        response = await axios.post(`${API}/raw-materials`, rawMaterial);
        alert(`تم إضافة المادة الخام بنجاح. كود الوحدة: ${response.data.unit_code}`);
      }

      fetchRawMaterials();
      setNewRawMaterial({
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        height: '',
        pieces_count: '',
        cost_per_mm: ''
      });
    } catch (error) {
      console.error('Error saving raw material:', error);
      alert('حدث خطأ في حفظ المادة الخام: ' + (error.response?.data?.detail || error.message));
    }
  };

  const clearAllRawMaterials = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع المواد الخام؟')) {
      return;
    }

    try {
      await axios.delete(`${API}/raw-materials/clear-all`);
      fetchRawMaterials();
      alert('تم حذف جميع المواد الخام');
    } catch (error) {
      console.error('Error clearing raw materials:', error);
      alert('حدث خطأ في حذف المواد الخام');
    }
  };

  const deleteRawMaterial = async (materialId) => {
    if (!confirm('هل أنت متأكد من حذف هذه المادة الخام؟')) {
      return;
    }

    try {
      await axios.delete(`${API}/raw-materials/${materialId}`);
      fetchRawMaterials();
      alert('تم حذف المادة الخام');
    } catch (error) {
      console.error('Error deleting raw material:', error);
      alert('حدث خطأ في حذف المادة الخام');
    }
  };

  const editRawMaterial = (material) => {
    // Fill the form with the material data for editing
    setNewRawMaterial({
      id: material.id,
      material_type: material.material_type,
      inner_diameter: material.inner_diameter.toString(),
      outer_diameter: material.outer_diameter.toString(),
      height: material.height.toString(),
      pieces_count: material.pieces_count.toString(),
      cost_per_mm: material.cost_per_mm.toString()
    });
  };

  const handleFileImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/excel/import/raw-materials`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      alert(response.data.message);
      fetchRawMaterials(); // Refresh the raw materials list
      event.target.value = ''; // Clear file input
    } catch (error) {
      console.error('Error importing file:', error);
      alert('حدث خطأ في استيراد الملف: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleFileExport = async () => {
    try {
      const response = await axios.get(`${API}/excel/export/raw-materials`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `raw_materials_export_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting file:', error);
      alert('حدث خطأ في تصدير الملف');
    }
  };

  const addFinishedProduct = async () => {
    if (!newFinishedProduct.inner_diameter || !newFinishedProduct.outer_diameter || !newFinishedProduct.height || !newFinishedProduct.quantity || !newFinishedProduct.unit_price) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      const finishedProduct = {
        seal_type: newFinishedProduct.seal_type,
        material_type: newFinishedProduct.material_type,
        inner_diameter: parseFloat(newFinishedProduct.inner_diameter),
        outer_diameter: parseFloat(newFinishedProduct.outer_diameter),
        height: parseFloat(newFinishedProduct.height),
        quantity: parseInt(newFinishedProduct.quantity),
        unit_price: parseFloat(newFinishedProduct.unit_price)
      };

      if (newFinishedProduct.id) {
        // Update existing product
        await axios.put(`${API}/finished-products/${newFinishedProduct.id}`, finishedProduct);
        alert('تم تحديث المنتج النهائي بنجاح');
      } else {
        // Add new product
        await axios.post(`${API}/finished-products`, finishedProduct);
        alert('تم إضافة المنتج النهائي بنجاح');
      }

      fetchFinishedProducts();
      setNewFinishedProduct({
        seal_type: 'RSL',
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        height: '',
        quantity: '',
        unit_price: ''
      });
    } catch (error) {
      console.error('Error saving finished product:', error);
      alert('حدث خطأ في حفظ المنتج النهائي');
    }
  };

  const editFinishedProduct = (product) => {
    // Fill the form with the product data for editing
    setNewFinishedProduct({
      id: product.id,
      seal_type: product.seal_type,
      material_type: product.material_type,
      inner_diameter: product.inner_diameter.toString(),
      outer_diameter: product.outer_diameter.toString(),
      height: product.height.toString(),
      quantity: product.quantity.toString(),
      unit_price: product.unit_price.toString()
    });
  };

  const deleteFinishedProduct = async (productId) => {
    if (!confirm('هل أنت متأكد من حذف هذا المنتج النهائي؟')) {
      return;
    }

    try {
      await axios.delete(`${API}/finished-products/${productId}`);
      fetchFinishedProducts();
      alert('تم حذف المنتج النهائي');
    } catch (error) {
      console.error('Error deleting finished product:', error);
      alert('حدث خطأ في حذف المنتج النهائي');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <h1 className="text-3xl font-bold mb-6">مخزن إنتاج</h1>

      {/* Raw Materials Section */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">مخزون المواد الخام</h3>
          <div className="flex space-x-2 space-x-reverse">
            <button
              onClick={clearAllRawMaterials}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              حذف الكل
            </button>
          </div>
        </div>

        {/* Import/Export Section */}
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h4 className="font-medium mb-4">📁 استيراد وتصدير المواد الخام</h4>
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <label className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 cursor-pointer">
                📤 استيراد من Excel
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileImport}
                  className="hidden"
                />
              </label>
              <span className="text-sm text-gray-600">(.xlsx أو .xls)</span>
            </div>

            <button
              onClick={handleFileExport}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              📥 تصدير إلى Excel
            </button>

            <div className="text-sm text-gray-600 bg-white p-2 rounded border">
              <strong>تنسيق الملف المطلوب:</strong><br />
              material_type, inner_diameter, outer_diameter, height, pieces_count, unit_code, cost_per_mm
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">نوع الخامة</label>
            <select
              value={newRawMaterial.material_type}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, material_type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {materialTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الداخلي</label>
            <input
              type="number"
              value={newRawMaterial.inner_diameter}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, inner_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الخارجي</label>
            <input
              type="number"
              value={newRawMaterial.outer_diameter}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, outer_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الارتفاع (مم)</label>
            <input
              type="number"
              value={newRawMaterial.height}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, height: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">عدد القطع</label>
            <input
              type="number"
              value={newRawMaterial.pieces_count}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, pieces_count: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">تكلفة المللي</label>
            <input
              type="number"
              step="0.01"
              value={newRawMaterial.cost_per_mm}
              onChange={(e) => setNewRawMaterial({ ...newRawMaterial, cost_per_mm: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>
        </div>

        <p className="text-sm text-gray-600 mt-4">
          ملاحظة: سيتم توليد كود الوحدة تلقائياً حسب نوع الخامة والمواصفات
        </p>

        <button
          onClick={addRawMaterial}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mb-4"
        >
          إضافة مادة خام
        </button>

        {/* حقل البحث */}
        <div className="mb-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="بحث في المواد الخام (نوع الخامة، كود الوحدة، المقاسات...)"
            className="w-full p-3 border border-gray-300 rounded-lg"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">نوع الخامة</th>
                <th className="border border-gray-300 p-2">القطر الداخلي</th>
                <th className="border border-gray-300 p-2">القطر الخارجي</th>
                <th className="border border-gray-300 p-2">الارتفاع</th>
                <th className="border border-gray-300 p-2">عدد القطع</th>
                <th className="border border-gray-300 p-2">كود الوحدة</th>
                <th className="border border-gray-300 p-2">تكلفة المللي</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredRawMaterials.map(material => (
                <tr key={material.id}>
                  <td className="border border-gray-300 p-2">{material.material_type}</td>
                  <td className="border border-gray-300 p-2">{material.inner_diameter}</td>
                  <td className="border border-gray-300 p-2">{material.outer_diameter}</td>
                  <td className="border border-gray-300 p-2">{material.height}</td>
                  <td className="border border-gray-300 p-2">{material.pieces_count}</td>
                  <td className="border border-gray-300 p-2">{material.unit_code}</td>
                  <td className="border border-gray-300 p-2">{material.cost_per_mm}</td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse">
                      <button
                        onClick={() => editRawMaterial(material)}
                        className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                        title="تحرير"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteRawMaterial(material.id)}
                        className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                        title="حذف"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Finished Products Section */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">مخزون الإنتاج التام</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">نوع السيل</label>
            <select
              value={newFinishedProduct.seal_type}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, seal_type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {sealTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">نوع الخامة</label>
            <select
              value={newFinishedProduct.material_type}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, material_type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {materialTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الداخلي</label>
            <input
              type="number"
              value={newFinishedProduct.inner_diameter}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, inner_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الخارجي</label>
            <input
              type="number"
              value={newFinishedProduct.outer_diameter}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, outer_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">ارتفاع السيل</label>
            <input
              type="number"
              value={newFinishedProduct.height}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, height: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الكمية</label>
            <input
              type="number"
              value={newFinishedProduct.quantity}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, quantity: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">سعر الوحدة</label>
            <input
              type="number"
              step="0.01"
              value={newFinishedProduct.unit_price}
              onChange={(e) => setNewFinishedProduct({ ...newFinishedProduct, unit_price: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>
        </div>

        <button
          onClick={addFinishedProduct}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 mb-4"
        >
          إضافة منتج نهائي
        </button>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">نوع السيل</th>
                <th className="border border-gray-300 p-2">نوع الخامة</th>
                <th className="border border-gray-300 p-2">القطر الداخلي</th>
                <th className="border border-gray-300 p-2">القطر الخارجي</th>
                <th className="border border-gray-300 p-2">الارتفاع</th>
                <th className="border border-gray-300 p-2">الكمية</th>
                <th className="border border-gray-300 p-2">سعر الوحدة</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredFinishedProducts.map(product => (
                <tr key={product.id}>
                  <td className="border border-gray-300 p-2">{product.seal_type}</td>
                  <td className="border border-gray-300 p-2">{product.material_type}</td>
                  <td className="border border-gray-300 p-2">{product.inner_diameter}</td>
                  <td className="border border-gray-300 p-2">{product.outer_diameter}</td>
                  <td className="border border-gray-300 p-2">{product.height}</td>
                  <td className="border border-gray-300 p-2">{product.quantity}</td>
                  <td className="border border-gray-300 p-2">{product.unit_price}</td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse">
                      <button
                        onClick={() => editFinishedProduct(product)}
                        className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                        title="تحرير"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteFinishedProduct(product.id)}
                        className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                        title="حذف"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Deferred Payments Component
const Deferred = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [unpaidInvoices, setUnpaidInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('نقدي');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // إجماليات لكل عميل
  const [customerTotals, setCustomerTotals] = useState({});

  useEffect(() => {
    fetchUnpaidInvoices();
    fetchCustomers();
  }, []);

  useEffect(() => {
    // حساب إجماليات العملاء
    const totals = {};
    filteredInvoices.forEach(invoice => {
      const customerName = invoice.customer_name;
      if (!totals[customerName]) {
        totals[customerName] = {
          totalAmount: 0,
          invoiceCount: 0
        };
      }
      totals[customerName].totalAmount += invoice.remaining_amount || invoice.total_amount;
      totals[customerName].invoiceCount += 1;
    });
    setCustomerTotals(totals);
  }, [unpaidInvoices, searchTerm]);

  // فلترة الفواتير حسب البحث
  const filteredInvoices = unpaidInvoices.filter(invoice =>
    invoice.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (invoice.invoice_title && invoice.invoice_title.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  useEffect(() => {
    fetchUnpaidInvoices();
    fetchCustomers();
  }, []);

  const fetchUnpaidInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      const invoices = response.data.filter(invoice =>
        // يجب أن تكون الفاتورة آجلة أو لها مبلغ مستحق
        (invoice.payment_method === 'آجل' || invoice.remaining_amount > 0) &&
        (invoice.status === 'غير مدفوعة' ||
          invoice.status === 'مدفوعة جزئياً' ||
          invoice.status === 'انتظار' ||
          invoice.remaining_amount > 0)
      );
      setUnpaidInvoices(invoices);
    } catch (error) {
      console.error('Error fetching unpaid invoices:', error);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      // Sort customers alphabetically by name
      const sortedCustomers = (response.data || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'ar')
      );
      setCustomers(sortedCustomers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'عميل غير محدد';
  };

  const makePayment = async () => {
    if (!selectedInvoice || !paymentAmount) {
      alert('الرجاء اختيار الفاتورة وإدخال المبلغ');
      return;
    }

    if (parseFloat(paymentAmount) > selectedInvoice.remaining_amount) {
      alert('المبلغ المدخل أكبر من المبلغ المستحق');
      return;
    }

    try {
      await axios.post(`${API}/payments`, {
        invoice_id: selectedInvoice.id,
        amount: parseFloat(paymentAmount),
        payment_method: paymentMethod,
        notes: paymentNotes
      });

      setPaymentAmount('');
      setPaymentNotes('');
      setSelectedInvoice(null);
      fetchUnpaidInvoices();
      alert('تم تسجيل الدفعة بنجاح');
    } catch (error) {
      console.error('Error making payment:', error);
      alert('حدث خطأ في تسجيل الدفعة');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-blue-600 mb-2 md:mb-0">الآجل - متابعة المدفوعات</h3>
        <div className="flex space-x-2 space-x-reverse">
          <button
            onClick={() => window.print()}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
            طباعة تقرير
          </button>
          <select className="border border-gray-300 rounded px-3 py-2">
            <option>يومي</option>
            <option>أسبوعي</option>
            <option>شهري</option>
            <option>سنوي</option>
          </select>
        </div>
      </div>

      {/* شريط البحث وإجماليات العملاء */}
      <div className="bg-gray-50 p-4 rounded-lg mb-4">
        <div className="mb-3">
          <input
            type="text"
            placeholder="بحث بالعميل أو رقم الفاتورة أو العنوان..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded"
          />
        </div>

        {/* عرض إجماليات العملاء */}
        {Object.keys(customerTotals).length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(customerTotals).map(([customerName, totals]) => (
              <div key={customerName} className="bg-white p-3 rounded border text-center">
                <div className="font-semibold text-blue-800 text-sm">{customerName}</div>
                <div className="text-xs text-blue-600">
                  {totals.invoiceCount} فاتورة
                </div>
                <div className="text-sm font-bold text-green-600">
                  {totals.totalAmount.toFixed(2)} {currency}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payment Form */}
      {selectedInvoice && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h3 className="text-lg font-semibold mb-4">تسجيل دفعة</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">رقم الفاتورة</label>
              <input
                type="text"
                value={selectedInvoice.invoice_number}
                disabled
                className="w-full p-2 border border-gray-300 rounded bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">العميل</label>
              <input
                type="text"
                value={selectedInvoice.customer_name}
                disabled
                className="w-full p-2 border border-gray-300 rounded bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">المبلغ المستحق</label>
              <input
                type="text"
                value={`${currency} ${selectedInvoice.remaining_amount?.toFixed(2) || '0.00'}`}
                disabled
                className="w-full p-2 border border-gray-300 rounded bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">مبلغ الدفعة</label>
              <input
                type="number"
                step="0.01"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">طريقة الدفع</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
              >
                <option value="نقدي">نقدي</option>
                <option value="فودافون 010">فودافون 010</option>
                <option value="كاش 0100">كاش 0100</option>
                <option value="انستاباي">انستاباي</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">ملاحظات</label>
              <input
                type="text"
                value={paymentNotes}
                onChange={(e) => setPaymentNotes(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="ملاحظات إضافية (اختياري)"
              />
            </div>
          </div>

          <div className="flex space-x-4 space-x-reverse">
            <button
              onClick={makePayment}
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
            >
              تسجيل الدفعة
            </button>
            <button
              onClick={() => setSelectedInvoice(null)}
              className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600"
            >
              إلغاء
            </button>
          </div>
        </div>
      )}

      {/* Unpaid Invoices */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">الفواتير غير المسددة</h3>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">رقم الفاتورة</th>
                <th className="border border-gray-300 p-2">العميل</th>
                <th className="border border-gray-300 p-2">التاريخ</th>
                <th className="border border-gray-300 p-2">الإجمالي</th>
                <th className="border border-gray-300 p-2">المدفوع</th>
                <th className="border border-gray-300 p-2">المستحق</th>
                <th className="border border-gray-300 p-2">الحالة</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td className="border border-gray-300 p-2">{invoice.invoice_number}</td>
                  <td className="border border-gray-300 p-2">{invoice.customer_name}</td>
                  <td className="border border-gray-300 p-2">
                    {new Date(invoice.date).toLocaleDateString('ar-EG')}
                  </td>
                  <td className="border border-gray-300 p-2">{currency} {invoice.total_amount?.toFixed(2) || '0.00'}</td>
                  <td className="border border-gray-300 p-2">{currency} {invoice.paid_amount?.toFixed(2) || '0.00'}</td>
                  <td className="border border-gray-300 p-2">
                    <span className="font-bold text-red-600">
                      {currency} {invoice.remaining_amount?.toFixed(2) || '0.00'}
                    </span>
                  </td>
                  <td className="border border-gray-300 p-2">
                    <span className={`px-2 py-1 rounded text-sm ${invoice.status === 'غير مدفوعة' ? 'bg-red-100 text-red-800' :
                      invoice.status === 'مدفوعة جزئياً' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                      {invoice.status_description || invoice.status}
                    </span>
                    {invoice.payment_method_used && (
                      <div className="text-xs text-gray-500 mt-1">
                        💳 {invoice.payment_method_used}
                      </div>
                    )}
                  </td>

                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse">
                      <button
                        onClick={() => setSelectedInvoice(invoice)}
                        className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                      >
                        عرض الدفعات
                      </button>
                      <button
                        onClick={() => setSelectedInvoice(invoice)}
                        className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                      >
                        دفع
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredInvoices.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              لا توجد فواتير غير مسددة
            </div>
          )}
        </div>

        {/* Summary */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-red-50 p-4 rounded">
            <h4 className="font-semibold text-red-800">إجمالي المبالغ المستحقة</h4>
            <p className="text-2xl font-bold text-red-600">
              {currency} {filteredInvoices.reduce((sum, inv) => sum + (inv.remaining_amount || 0), 0).toFixed(2)}
            </p>
          </div>

          <div className="bg-yellow-50 p-4 rounded">
            <h4 className="font-semibold text-yellow-800">عدد الفواتير المعلقة</h4>
            <p className="text-2xl font-bold text-yellow-600">{filteredInvoices.length}</p>
          </div>

          <div className="bg-blue-50 p-4 rounded">
            <h4 className="font-semibold text-blue-800">إجمالي المبلغ الأصلي</h4>
            <p className="text-2xl font-bold text-blue-600">
              {currency} {filteredInvoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Expenses Component
const Expenses = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [expenses, setExpenses] = useState([]);
  const [newExpense, setNewExpense] = useState({
    description: '',
    amount: '',
    category: 'خامات'
  });

  const expenseCategories = ['خامات', 'رواتب', 'كهرباء', 'صيانة', 'أخرى'];

  useEffect(() => {
    fetchExpenses();
  }, []);

  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses`);
      setExpenses(response.data);
    } catch (error) {
      console.error('Error fetching expenses:', error);
    }
  };

  const addExpense = async () => {
    if (!newExpense.description || !newExpense.amount) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      await axios.post(`${API}/expenses`, {
        ...newExpense,
        amount: parseFloat(newExpense.amount)
      });

      setNewExpense({
        description: '',
        amount: '',
        category: 'خامات'
      });

      fetchExpenses();
      alert('تم إضافة المصروف بنجاح');
    } catch (error) {
      console.error('Error adding expense:', error);
      alert('حدث خطأ في إضافة المصروف');
    }
  };

  const deleteExpense = async (expenseId) => {
    if (!confirm('هل أنت متأكد من حذف هذا المصروف؟')) return;

    try {
      await axios.delete(`${API}/expenses/${expenseId}`);
      fetchExpenses();
      alert('تم حذف المصروف بنجاح');
    } catch (error) {
      console.error('Error deleting expense:', error);
      alert('حدث خطأ في حذف المصروف');
    }
  };

  const getTotalExpenses = () => {
    return expenses.reduce((sum, expense) => sum + expense.amount, 0);
  };

  const getExpensesByCategory = () => {
    const byCategory = {};
    expenseCategories.forEach(cat => {
      byCategory[cat] = expenses
        .filter(exp => exp.category === cat)
        .reduce((sum, exp) => sum + exp.amount, 0);
    });
    return byCategory;
  };

  const clearAllExpenses = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع المصروفات؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    try {
      await axios.delete(`${API}/expenses/clear-all`);
      fetchExpenses();
      alert('تم حذف جميع المصروفات');
    } catch (error) {
      console.error('Error clearing expenses:', error);
      alert('حدث خطأ في حذف البيانات');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">المصروفات</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button
            onClick={clearAllExpenses}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            حذف الكل
          </button>
          <button
            onClick={fetchExpenses}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            طباعة تقرير
          </button>
          <select className="border border-gray-300 rounded px-3 py-2">
            <option>يومي</option>
            <option>أسبوعي</option>
            <option>شهري</option>
            <option>سنوي</option>
          </select>
        </div>
      </div>

      {/* Add New Expense */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">إضافة مصروف جديد</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">وصف المصروف</label>
            <input
              type="text"
              value={newExpense.description}
              onChange={(e) => setNewExpense({ ...newExpense, description: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="مثال: شراء خامات، كهرباء المصنع"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">المبلغ</label>
            <input
              type="number"
              step="0.01"
              value={newExpense.amount}
              onChange={(e) => setNewExpense({ ...newExpense, amount: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الفئة</label>
            <select
              value={newExpense.category}
              onChange={(e) => setNewExpense({ ...newExpense, category: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {expenseCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={addExpense}
          className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
        >
          إضافة المصروف
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-red-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800 mb-2">إجمالي المصروفات</h3>
          <p className="text-3xl font-bold text-red-600">
            {currency} {getTotalExpenses().toFixed(2)}
          </p>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">عدد المصروفات</h3>
          <p className="text-3xl font-bold text-blue-600">{expenses.length}</p>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">متوسط المصروف</h3>
          <p className="text-3xl font-bold text-yellow-600">
            {currency} {expenses.length > 0 ? (getTotalExpenses() / expenses.length).toFixed(2) : '0.00'}
          </p>
        </div>
      </div>

      {/* Expenses by Category */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">المصروفات حسب الفئة</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {Object.entries(getExpensesByCategory()).map(([category, amount]) => (
            <div key={category} className="text-center p-4 border rounded">
              <h4 className="font-medium text-gray-700">{category}</h4>
              <p className="text-xl font-bold text-blue-600">{currency} {amount.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Expenses List */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">المصروفات</h3>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">الوصف</th>
                <th className="border border-gray-300 p-2">المبلغ</th>
                <th className="border border-gray-300 p-2">الفئة</th>
                <th className="border border-gray-300 p-2">التاريخ</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((expense) => (
                <tr key={expense.id}>
                  <td className="border border-gray-300 p-2">{expense.description}</td>
                  <td className="border border-gray-300 p-2">
                    <span className="font-semibold text-red-600">
                      {currency} {expense.amount.toFixed(2)}
                    </span>
                  </td>
                  <td className="border border-gray-300 p-2">
                    <span className={`px-2 py-1 rounded text-sm ${expense.category === 'خامات' ? 'bg-blue-100 text-blue-800' :
                      expense.category === 'رواتب' ? 'bg-green-100 text-green-800' :
                        expense.category === 'كهرباء' ? 'bg-yellow-100 text-yellow-800' :
                          expense.category === 'صيانة' ? 'bg-purple-100 text-purple-800' :
                            'bg-gray-100 text-gray-800'
                      }`}>
                      {expense.category}
                    </span>
                  </td>
                  <td className="border border-gray-300 p-2">
                    {new Date(expense.date).toLocaleDateString('ar-EG')}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <button
                      onClick={() => deleteExpense(expense.id)}
                      className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600">
                      حذف
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {expenses.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              لا توجد مصروفات مسجلة
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Revenue Component
const Revenue = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [revenueData, setRevenueData] = useState({
    total_revenue: 0,
    total_expenses: 0,
    material_cost: 0,
    profit: 0
  });
  const [period, setPeriod] = useState('daily');

  useEffect(() => {
    fetchRevenueData();
  }, [period]);

  const fetchRevenueData = async () => {
    try {
      const response = await axios.get(`${API}/reports/revenue?period=${period}`);
      setRevenueData(response.data);
    } catch (error) {
      console.error('Error fetching revenue data:', error);
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">الإيرادات</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            حذف الكل
          </button>
          <button
            onClick={fetchRevenueData}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            طباعة تقرير
          </button>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2">
            <option value="daily">اليوم</option>
            <option value="weekly">الأسبوع</option>
            <option value="monthly">الشهر</option>
            <option value="yearly">السنة</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Revenue Cards */}
        <div className="bg-green-50 p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-green-800 text-center mb-2">إجمالي الإيرادات</h3>
          <p className="text-3xl font-bold text-green-600 text-center">
            {currency} {revenueData.total_revenue?.toFixed(2) || '0.00'}
          </p>
        </div>

        <div className="bg-red-50 p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-red-800 text-center mb-2">إجمالي المصروفات</h3>
          <p className="text-3xl font-bold text-red-600 text-center">
            {currency} {revenueData.total_expenses?.toFixed(2) || '0.00'}
          </p>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-yellow-800 text-center mb-2">تكلفة الخامات</h3>
          <p className="text-3xl font-bold text-yellow-600 text-center">
            {currency} {revenueData.material_cost?.toFixed(2) || '0.00'}
          </p>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-blue-800 text-center mb-2">صافي الربح</h3>
          <p className={`text-3xl font-bold text-center ${(revenueData.profit || 0) >= 0 ? 'text-blue-600' : 'text-red-600'
            }`}>
            {currency} {revenueData.profit?.toFixed(2) || '0.00'}
          </p>
        </div>
      </div>

      {/* Summary Table */}
      <div className="bg-white p-6 rounded-lg shadow-md mt-6">
        <h3 className="text-lg font-semibold mb-4">تقرير الإيرادات - {
          period === 'daily' ? 'يومي' :
            period === 'weekly' ? 'أسبوعي' :
              period === 'monthly' ? 'شهري' : 'سنوي'
        }</h3>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-3">البيان</th>
                <th className="border border-gray-300 p-3">المبلغ ({currency})</th>
                <th className="border border-gray-300 p-3">النسبة المئوية</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-gray-300 p-3 font-semibold">إجمالي الإيرادات</td>
                <td className="border border-gray-300 p-3 text-green-600 font-bold">
                  {revenueData.total_revenue?.toFixed(2) || '0.00'}
                </td>
                <td className="border border-gray-300 p-3">100%</td>
              </tr>
              <tr>
                <td className="border border-gray-300 p-3">تكلفة الخامات</td>
                <td className="border border-gray-300 p-3 text-yellow-600 font-semibold">
                  -{revenueData.material_cost?.toFixed(2) || '0.00'}
                </td>
                <td className="border border-gray-300 p-3">
                  {revenueData.total_revenue > 0
                    ? ((revenueData.material_cost / revenueData.total_revenue) * 100).toFixed(1)
                    : '0.0'}%
                </td>
              </tr>
              <tr>
                <td className="border border-gray-300 p-3">مصروفات أخرى</td>
                <td className="border border-gray-300 p-3 text-red-600 font-semibold">
                  -{((revenueData.total_expenses || 0) - (revenueData.material_cost || 0)).toFixed(2)}
                </td>
                <td className="border border-gray-300 p-3">
                  {revenueData.total_revenue > 0
                    ? (((revenueData.total_expenses - revenueData.material_cost) / revenueData.total_revenue) * 100).toFixed(1)
                    : '0.0'}%
                </td>
              </tr>
              <tr className="bg-blue-50">
                <td className="border border-gray-300 p-3 font-bold">صافي الربح</td>
                <td className={`border border-gray-300 p-3 font-bold ${(revenueData.profit || 0) >= 0 ? 'text-blue-600' : 'text-red-600'
                  }`}>
                  {revenueData.profit?.toFixed(2) || '0.00'}
                </td>
                <td className="border border-gray-300 p-3 font-bold">
                  {revenueData.total_revenue > 0
                    ? ((revenueData.profit / revenueData.total_revenue) * 100).toFixed(1)
                    : '0.0'}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance Indicators */}
      <div className="bg-white p-6 rounded-lg shadow-md mt-6">
        <h3 className="text-lg font-semibold mb-4">مؤشرات الأداء</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 border rounded">
            <h4 className="font-medium text-gray-700 mb-2">هامش الربح</h4>
            <p className={`text-2xl font-bold ${(revenueData.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
              {revenueData.total_revenue > 0
                ? ((revenueData.profit / revenueData.total_revenue) * 100).toFixed(1)
                : '0.0'}%
            </p>
          </div>

          <div className="text-center p-4 border rounded">
            <h4 className="font-medium text-gray-700 mb-2">نسبة تكلفة الخامات</h4>
            <p className="text-2xl font-bold text-yellow-600">
              {revenueData.total_revenue > 0
                ? ((revenueData.material_cost / revenueData.total_revenue) * 100).toFixed(1)
                : '0.0'}%
            </p>
          </div>

          <div className="text-center p-4 border rounded">
            <h4 className="font-medium text-gray-700 mb-2">نسبة المصروفات الإجمالية</h4>
            <p className="text-2xl font-bold text-red-600">
              {revenueData.total_revenue > 0
                ? ((revenueData.total_expenses / revenueData.total_revenue) * 100).toFixed(1)
                : '0.0'}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Invoices Component
const Invoices = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [editForm, setEditForm] = useState({
    invoice_title: '',
    supervisor_name: '',
    customer_name: '',
    payment_method: 'نقدي',
    discount_type: 'amount',
    discount_value: 0,
    items: [],
    notes: ''
  });

  // Password protection states
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [operationPassword, setOperationPassword] = useState('');
  const [pendingOperation, setPendingOperation] = useState(null); // {type: 'cancel'|'edit'|'changePayment', data: ...}

  // Edit history states
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [editHistory, setEditHistory] = useState([]);
  const [historyInvoiceId, setHistoryInvoiceId] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    fetchInvoices();
    fetchCustomers();
  }, []);

  const fetchInvoices = async () => {
    try {
      console.log('Fetching invoices...');
      const response = await axios.get(`${API}/invoices`);
      console.log('Invoices fetched:', response.data.length, 'invoices');
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
      alert('خطأ في تحميل الفواتير: ' + (error.response?.data?.detail || error.message));
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      // Sort customers alphabetically by name
      const sortedCustomers = (response.data || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'ar')
      );
      setCustomers(sortedCustomers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  // Request password for operation
  const requestPasswordFor = (operationType, operationData) => {
    setPendingOperation({ type: operationType, data: operationData });
    setOperationPassword('');
    setShowPasswordModal(true);
  };

  // Execute operation after password verification
  const executeOperation = async () => {
    if (!operationPassword) {
      alert('الرجاء إدخال كلمة المرور');
      return;
    }

    if (!pendingOperation) {
      alert('لا توجد عملية معلقة');
      return;
    }

    try {
      if (pendingOperation.type === 'cancel') {
        await executeCancelInvoice(pendingOperation.data, operationPassword);
      } else if (pendingOperation.type === 'edit') {
        await executeUpdateInvoice(operationPassword);
      } else if (pendingOperation.type === 'changePayment') {
        await executeChangePaymentMethod(pendingOperation.data.invoiceId, pendingOperation.data.newMethod, operationPassword);
      }

      setShowPasswordModal(false);
      setPendingOperation(null);
      setOperationPassword('');
    } catch (error) {
      console.error('Operation error:', error);
      alert(error.response?.data?.detail || error.message || 'حدث خطأ في العملية');
    }
  };

  // Execute cancel with password
  const executeCancelInvoice = async (invoiceId, password) => {
    const response = await axios.delete(`${API}/invoices/${invoiceId}/cancel`, {
      params: {
        password: password,
        username: user?.username
      }
    });

    alert(response.data.message);
    fetchInvoices();
  };

  // Execute update with password
  const executeUpdateInvoice = async (password) => {
    const response = await axios.put(
      `${API}/invoices/${editingInvoice}`,
      editForm,
      { params: { password: password } }
    );

    alert('تم تحديث الفاتورة بنجاح');
    setEditingInvoice(null);
    fetchInvoices();
  };

  // Execute change payment method with password
  const executeChangePaymentMethod = async (invoiceId, newMethod, password) => {
    await axios.put(`${API}/invoices/${invoiceId}/change-payment-method`, null, {
      params: {
        new_payment_method: newMethod,
        password: password
      }
    });

    alert('تم تغيير طريقة الدفع بنجاح');
    fetchInvoices();
  };

  // Change payment method function
  const changePaymentMethod = async (invoiceId) => {
    const paymentMethods = [
      { value: 'نقدي', label: 'نقدي' },
      { value: 'آجل', label: 'آجل' },
      { value: 'فودافون 010', label: 'فودافون 010' },
      { value: 'كاش 0100', label: 'كاش 0100' },
      { value: 'انستاباي', label: 'انستاباي' },
      { value: 'يد الصاوي', label: 'يد الصاوي' }
    ];

    const invoice = invoices.find(inv => inv.id === invoiceId);
    if (!invoice) {
      alert('الفاتورة غير موجودة');
      return;
    }

    // منع تحويل الفواتير المدفوعة جزئياً
    if (invoice.paid_amount > 0 && invoice.remaining_amount > 0) {
      alert('لا يمكن تحويل طريقة دفع فاتورة مدفوعة جزئياً');
      return;
    }

    // إنشاء نافذة حوار مخصصة للاختيار
    const modalHtml = `
      <div id="paymentMethodModal" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        direction: rtl;
      ">
        <div style="
          background: white;
          padding: 30px;
          border-radius: 10px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          min-width: 400px;
          text-align: center;
        ">
          <h3 style="margin-bottom: 20px; color: #333;">تغيير طريقة الدفع</h3>
          <p style="margin-bottom: 15px;">الفاتورة: <strong>${invoice.invoice_number}</strong></p>
          <p style="margin-bottom: 20px;">طريقة الدفع الحالية: <strong style="color: #e74c3c;">${invoice.payment_method}</strong></p>
          <div style="margin-bottom: 20px;">
            <label style="display: block; margin-bottom: 10px; font-weight: bold;">اختر طريقة الدفع الجديدة:</label>
            <select id="newPaymentMethod" style="
              width: 100%;
              padding: 10px;
              border: 2px solid #ddd;
              border-radius: 5px;
              font-size: 16px;
              direction: rtl;
            ">
              <option value="">-- اختر طريقة الدفع --</option>
              ${paymentMethods
        .filter(method => method.value !== invoice.payment_method)
        .map(method => `<option value="${method.value}">${method.label}</option>`)
        .join('')}
            </select>
          </div>
          <div style="display: flex; gap: 10px; justify-content: center;">
            <button id="confirmChange" style="
              background: #27ae60;
              color: white;
              border: none;
              padding: 10px 20px;
              border-radius: 5px;
              cursor: pointer;
              font-size: 16px;
            ">تأكيد التغيير</button>
            <button id="cancelChange" style="
              background: #e74c3c;
              color: white;
              border: none;
              padding: 10px 20px;
              border-radius: 5px;
              cursor: pointer;
              font-size: 16px;
            ">إلغاء</button>
          </div>
        </div>
      </div>
    `;

    // إضافة النافذة للصفحة
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // إضافة أحداث الأزرار
    const modal = document.getElementById('paymentMethodModal');
    const selectElement = document.getElementById('newPaymentMethod');
    const confirmBtn = document.getElementById('confirmChange');
    const cancelBtn = document.getElementById('cancelChange');

    // إغلاق النافذة
    const closeModal = () => {
      if (modal && modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
    };

    // زر الإلغاء
    cancelBtn.onclick = closeModal;

    // النقر خارج النافذة
    modal.onclick = (e) => {
      if (e.target === modal) {
        closeModal();
      }
    };

    // زر التأكيد
    confirmBtn.onclick = async () => {
      const newMethod = selectElement.value;

      if (!newMethod) {
        alert('الرجاء اختيار طريقة دفع جديدة');
        return;
      }

      if (newMethod === invoice.payment_method) {
        alert('طريقة الدفع هي نفسها بالفعل');
        return;
      }

      if (!confirm(`هل أنت متأكد من تحويل طريقة الدفع من "${invoice.payment_method}" إلى "${newMethod}"؟\n\nسيتم تحديث الخزينة والحسابات تلقائياً.\n\nيتطلب كلمة مرور للتأكيد`)) {
        return;
      }

      closeModal();
      // Request password
      requestPasswordFor('changePayment', { invoiceId, newMethod });
    };
  };

  // Cancel invoice function
  const cancelInvoice = async (invoiceId) => {
    const invoice = invoices.find(inv => inv.id === invoiceId);
    if (!invoice) {
      alert('الفاتورة غير موجودة');
      return;
    }

    const confirmMessage = `هل أنت متأكد من إلغاء الفاتورة ${invoice.invoice_number}؟\n\nسيتم:\n- إرجاع المواد المستخدمة إلى المخزن\n- عمل معاملة عكسية في الخزينة\n- نقل الفاتورة للمحذوفة\n\nيتطلب كلمة مرور للتأكيد`;

    if (!confirm(confirmMessage)) {
      return;
    }

    // Request password
    requestPasswordFor('cancel', invoiceId);
  };

  const startEditInvoice = (invoice) => {
    setEditingInvoice(invoice.id);
    setEditForm({
      invoice_title: invoice.invoice_title || '',
      supervisor_name: invoice.supervisor_name || '',
      customer_name: invoice.customer_name || '',
      payment_method: invoice.payment_method || 'نقدي',
      discount_type: invoice.discount_type || 'amount',
      discount_value: invoice.discount_value || 0,
      items: invoice.items || [],
      notes: invoice.notes || ''
    });
  };

  const cancelEdit = () => {
    setEditingInvoice(null);
    setEditForm({
      invoice_title: '',
      supervisor_name: '',
      customer_name: '',
      payment_method: 'نقدي',
      discount_type: 'amount',
      discount_value: 0,
      items: [],
      notes: ''
    });
  };

  const saveInvoiceEdit = async () => {
    if (!editForm.customer_name.trim()) {
      alert('الرجاء إدخال اسم العميل');
      return;
    }

    try {
      console.log('Saving invoice edit for ID:', editingInvoice);
      console.log('Edit form data:', editForm);

      // Calculate totals
      const subtotal = editForm.items.reduce((sum, item) => sum + (item.total_price || 0), 0);
      let discountAmount = 0;

      if (editForm.discount_type === 'percentage') {
        discountAmount = (subtotal * parseFloat(editForm.discount_value || 0)) / 100;
      } else {
        discountAmount = parseFloat(editForm.discount_value || 0);
      }

      const totalAfterDiscount = subtotal - discountAmount;

      const updatedInvoice = {
        ...editForm,
        subtotal: subtotal,
        discount: discountAmount,
        total_after_discount: totalAfterDiscount,
        total_amount: totalAfterDiscount
      };

      console.log('Sending update to backend:', updatedInvoice);

      // Store the edit form for password-protected execution
      setEditForm(updatedInvoice);

      // Request password
      requestPasswordFor('edit', null);
    } catch (error) {
      console.error('Error updating invoice:', error);
      console.error('Error response:', error.response?.data);
      alert('حدث خطأ في تحديث الفاتورة: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Edit History functions
  const fetchEditHistory = async (invoiceId) => {
    setHistoryLoading(true);
    setHistoryInvoiceId(invoiceId);
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/history`);
      setEditHistory(response.data || []);
      setShowHistoryModal(true);
    } catch (error) {
      console.error('Error fetching edit history:', error);
      alert('حدث خطأ في جلب سجل التعديلات');
    } finally {
      setHistoryLoading(false);
    }
  };

  const revertToVersion = async (historyId) => {
    if (!window.confirm('هل أنت متأكد من التراجع عن هذا التعديل؟ سيتم استعادة النسخة السابقة.')) return;
    try {
      await axios.post(`${API}/invoices/${historyInvoiceId}/revert/${historyId}`);
      alert('تم التراجع عن التعديل بنجاح');
      setShowHistoryModal(false);
      fetchInvoices();
    } catch (error) {
      console.error('Error reverting:', error);
      alert('حدث خطأ في التراجع: ' + (error.response?.data?.detail || error.message));
    }
  };

  const updateInvoiceStatus = async (invoiceId, newStatus) => {
    try {
      await axios.put(`${API}/invoices/${invoiceId}/status`,
        { status: newStatus }, {
        headers: { 'Content-Type': 'application/json' }
      });
      fetchInvoices();
      alert('تم تحديث حالة الفاتورة');
    } catch (error) {
      console.error('Error updating invoice status:', error);
      alert('حدث خطأ في تحديث حالة الفاتورة');
    }
  };

  const printInvoice = async (invoice) => {
    // Fetch company settings
    let s = {};
    try {
      const res = await axios.get(`${API}/settings`);
      s = res.data;
    } catch (e) { console.error('Settings fetch error:', e); }
    const cur = s.currency || 'ج.م';
    const lang = s.invoice_language || 'ar';
    const isEn = lang === 'en';
    const dir = isEn ? 'ltr' : 'rtl';
    const textAlign = isEn ? 'left' : 'right';
    // Use English fields when available for English invoice, fallback to Arabic
    const companyNameFull = isEn && s.company_name_full_en ? s.company_name_full_en : (s.company_name_full || 'شركة ماستر سيل');
    const companySubtitle = isEn && s.company_subtitle_en ? s.company_subtitle_en : (s.company_subtitle || 'تصنيع جميع أنواع الأويل سيل');
    const companyDetails1 = isEn && s.company_details_1_en ? s.company_details_1_en : (s.company_details_1 || 'جميع الأقطار حتى ٥٠٠مل');
    const companyDetails2 = isEn && s.company_details_2_en ? s.company_details_2_en : (s.company_details_2 || 'هيدروليك - نيوماتيك');
    const companyAddress = isEn && s.company_address_en ? s.company_address_en : (s.company_address || 'الحرفيين - السلام - أمام السوبر جيت');
    const companyMobile = isEn && s.company_mobile_en ? s.company_mobile_en : (s.company_mobile || '٠١٠٢٠٦٣٠٦٧٧ - ٠١٠٦٢٣٩٠٨٧٠');
    const companyLandline = isEn && s.company_landline_en ? s.company_landline_en : (s.company_landline || '٠١٠٢٠٦٣٠٦٧٧');
    const logoUrl = s.logo_url || 'https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg';
    const printContent = `
      <!DOCTYPE html>
      <html dir="${dir}">
      <head>
        <meta charset="UTF-8">
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            direction: ${dir};
            font-size: 15px;
          }
          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
          }
          .company-info {
            text-align: ${textAlign};
          }
          .company-name {
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin: 0;
          }
          .company-subtitle {
            font-size: 20px;
            margin: 5px 0;
            color: #666;
          }
          .company-details {
            font-size: 16px;
            margin: 2px 0;
            color: #333;
          }
          .logo-section {
            text-align: center;
            flex: 1;
          }
          .invoice-title {
            font-size: 22px;
            font-weight: bold;
            background-color: #ff4444;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            display: inline-block;
            margin-bottom: 10px;
          }
          .invoice-number {
            font-size: 20px;
            font-weight: bold;
            color: #ff4444;
          }
          .customer-info {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
          }
          .customer-details {
            text-align: ${textAlign};
          }
          .date-info {
            text-align: ${isEn ? 'right' : 'left'};
          }
          .products-table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid #000;
            margin: 20px 0;
          }
          .products-table th,
          .products-table td {
            border: 1px solid #000;
            padding: 8px;
            text-align: center;
          }
          .products-table th {
            background-color: #f0f0f0;
            font-weight: bold;
          }
          .footer {
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 15px;
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #666;
          }
          .total-section {
            text-align: ${isEn ? 'right' : 'left'};
            margin-top: 10px;
          }
          .total-amount {
            font-size: 20px;
            font-weight: bold;
            border: 2px solid #000;
            padding: 10px;
            display: inline-block;
            background-color: #f9f9f9;
          }
          @media print {
            body { margin: 0; padding: 10px; }
          }
        </style>
      </head>
      <body>
        <!-- Header Section -->
        <div class="header">
          <div class="company-info">
            <h1 class="company-name">${companyNameFull}</h1>
            <p class="company-subtitle">${companySubtitle}</p>
            <p class="company-details">${companyDetails1}</p>
            <p class="company-details">${companyDetails2}</p>
          </div>
          
          <div class="logo-section">
            <img src="${logoUrl}" 
                 alt="Logo" 
                 style="max-width: 120px; max-height: 80px; margin-bottom: 10px;">
            <div class="invoice-title">${isEn ? (invoice.invoice_title === 'فاتورة' ? 'Invoice' : invoice.invoice_title === 'عرض سعر' ? 'Quotation' : invoice.invoice_title || 'Quotation') : (invoice.invoice_title || 'عرض سعر')}</div>
            <div class="invoice-number">${invoice.invoice_number}</div>
          </div>
        </div>

        <!-- Customer and Date Info -->
        <div class="customer-info">
          <div class="customer-details">
            <p><strong>${isEn ? 'To:' : 'السادة:'}</strong> ${invoice.customer_name}</p>
            <p><strong>${isEn ? 'Address:' : 'العنوان:'}</strong> ${invoice.customer_address || '........................'}</p>
          </div>
          <div class="date-info">
            <p><strong>${isEn ? 'Date:' : 'تحرير في:'}</strong> ${isEn ? new Date(invoice.date).toLocaleDateString('en-GB') : new Date(invoice.date).toLocaleDateString('ar-EG')}</p>
            ${isEn ? '' : `<p><strong>Date:</strong> ${new Date(invoice.date).toLocaleDateString('en-GB')}</p>`}
          </div>
        </div>

        <!-- Products Table -->
        <table class="products-table">
          <thead>
            <tr>
              <th style="width: 60px;">${isEn ? 'Item' : 'المسلسل<br>Item'}</th>
              <th style="width: 80px;">${isEn ? 'Qty' : 'الكمية<br>QTY'}</th>
              <th style="width: 200px;">${isEn ? 'Description' : 'Description<br>المواصفات'}</th>
              <th style="width: 100px;">${isEn ? 'Unit Price' : 'سعر الوحدة<br>Unit Price'}</th>
              <th style="width: 100px;">${isEn ? 'Total' : 'إجمالي<br>Total'}</th>
            </tr>
          </thead>
          <tbody>
            ${invoice.items.map((item, index) => `
              <tr>
                <td>${index + 1}</td>
                <td>${item.quantity}</td>
                <td style="text-align: ${textAlign};">
                  ${item.local_product_details ?
        `${item.local_product_details.product_size} - ${item.local_product_details.product_type}` :
        `${item.seal_type} - ${item.material_type}<br>
                    <small>${item.inner_diameter} × ${item.outer_diameter} × ${item.height} ${isEn ? 'mm' : 'مم'}${item.wall_height ? ` (${isEn ? 'wall height' : 'ارتفاع الحيطة'}: ${item.wall_height} ${isEn ? 'mm' : 'مم'})` : ""}</small>`
      }
                </td>
                <td>${cur} ${item.unit_price.toFixed(2)}</td>
                <td>${cur} ${item.total_price.toFixed(2)}</td>
              </tr>
            `).join('')}
            <!-- Empty rows for additional items -->
            ${Array.from({ length: Math.max(0, 8 - invoice.items.length) }, (_, i) => `
              <tr style="height: 40px;">
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <!-- Total Section -->
        <div class="total-section">
          <div style="text-align: ${isEn ? 'right' : 'left'}; margin-bottom: 10px;">
            ${invoice.subtotal ? `
              <div style="margin-bottom: 5px;">
                <span>${isEn ? 'Subtotal' : 'المجموع الفرعي'}: ${cur} ${invoice.subtotal.toFixed(2)}</span>
              </div>
            ` : ''}
            ${invoice.discount && invoice.discount > 0 ? `
              <div style="margin-bottom: 5px; color: #d32f2f;">
                <span>${isEn ? 'Discount' : 'الخصم'}: - ${cur} ${invoice.discount.toFixed(2)}</span>
                ${invoice.discount_type === 'percentage' && invoice.discount_value ?
          ` <small>(${invoice.discount_value}%)</small>` : ''}
              </div>
              <hr style="margin: 5px 0; border: 1px solid #000;">
            ` : ''}
          </div>
          <div class="total-amount">
            ${isEn ? 'Grand Total' : 'الإجمالي النهائي'}: ${cur} ${(invoice.total_after_discount || invoice.total_amount).toFixed(2)}
          </div>
        </div>

        <!-- Additional Info -->
        <div style="margin-top: 20px; text-align: center; font-size: 13px;">
          <p><strong>${isEn ? 'Note:' : 'ملحوظة:'}</strong> ${isEn ? 'Amount in words:' : 'فقط وقدره'}</p>
          <div style="height: 30px; border-bottom: 1px solid #000; margin: 10px 40px;"></div>
        </div>

        <!-- Footer -->
        <div class="footer">
          <div>
            <p><strong>${isEn ? 'Signature:' : 'التوقيع:'}</strong></p>
            <p>${isEn ? 'Mobile' : 'موبايل'}: ${companyMobile}</p>
            <p>${isEn ? 'Phone' : 'تليفون'}: ${companyLandline}</p>
          </div>
          <div style="text-align: ${isEn ? 'right' : 'left'};">
            <p><strong>${isEn ? 'Received by:' : 'المستلم:'}</strong></p>
            <p>${companyAddress}</p>
            <p>${isEn ? 'Mobile' : 'موبايل'}: ${companyMobile}</p>
          </div>
        </div>

        <!-- Note -->
        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
          <p>${isEn ? 'The buyer acknowledges that the goods have been inspected and accepted' : 'يقر المشتري بأنه قام بمعاينة البضاعة وقبولها'}</p>
        </div>
      </body>
      </html>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  };

  const clearAllInvoices = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع الفواتير؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    try {
      await axios.delete(`${API}/invoices/clear-all`);
      fetchInvoices();
      alert('تم حذف جميع الفواتير');
    } catch (error) {
      console.error('Error clearing invoices:', error);
      alert('حدث خطأ في حذف البيانات');
    }
  };

  const filteredInvoices = invoices.filter(invoice => {
    const matchesStatus = filterStatus === '' || invoice.status === filterStatus;
    const matchesSearch = searchTerm === '' ||
      invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.customer_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">الفواتير</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button
            onClick={clearAllInvoices}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            حذف الكل
          </button>
          <button
            onClick={fetchInvoices}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            طباعة تقرير
          </button>
          <select className="border border-gray-300 rounded px-3 py-2">
            <option>يومي</option>
            <option>أسبوعي</option>
            <option>شهري</option>
            <option>سنوي</option>
          </select>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">البحث</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="رقم الفاتورة أو اسم العميل"
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">فلترة حسب الحالة</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="">جميع الحالات</option>
              <option value="مدفوعة">مدفوعة</option>
              <option value="غير مدفوعة">غير مدفوعة</option>
              <option value="مدفوعة جزئياً">مدفوعة جزئياً</option>
              <option value="انتظار">انتظار</option>
              <option value="تم التنفيذ">تم التنفيذ</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => { setSearchTerm(''); setFilterStatus(''); }}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              مسح الفلاتر
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg text-center">
          <h3 className="font-semibold text-blue-800">إجمالي الفواتير</h3>
          <p className="text-2xl font-bold text-blue-600">{invoices.length}</p>
        </div>

        <div className="bg-green-50 p-4 rounded-lg text-center">
          <h3 className="font-semibold text-green-800">المدفوعة</h3>
          <p className="text-2xl font-bold text-green-600">
            {invoices.filter(inv => inv.status === 'مدفوعة').length}
          </p>
        </div>

        <div className="bg-red-50 p-4 rounded-lg text-center">
          <h3 className="font-semibold text-red-800">غير المدفوعة</h3>
          <p className="text-2xl font-bold text-red-600">
            {invoices.filter(inv => inv.status === 'غير مدفوعة').length}
          </p>
        </div>

        <div className="bg-yellow-50 p-4 rounded-lg text-center">
          <h3 className="font-semibold text-yellow-800">الإجمالي</h3>
          <p className="text-2xl font-bold text-yellow-600">
            {currency} {invoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">جميع الفواتير</h3>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">رقم الفاتورة</th>
                <th className="border border-gray-300 p-2">العميل</th>
                <th className="border border-gray-300 p-2">التاريخ</th>
                <th className="border border-gray-300 p-2">طريقة الدفع</th>
                <th className="border border-gray-300 p-2">المجموع الفرعي</th>
                <th className="border border-gray-300 p-2">الخصم</th>
                <th className="border border-gray-300 p-2">الإجمالي النهائي</th>
                <th className="border border-gray-300 p-2">الحالة</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td className="border border-gray-300 p-2 font-semibold">
                    {invoice.invoice_number}
                  </td>
                  <td className="border border-gray-300 p-2">{invoice.customer_name}</td>
                  <td className="border border-gray-300 p-2">
                    {new Date(invoice.date).toLocaleDateString('ar-EG')}
                  </td>
                  <td className="border border-gray-300 p-2">{invoice.payment_method}</td>
                  <td className="border border-gray-300 p-2 font-semibold">
                    {currency} {invoice.subtotal?.toFixed(2) || (invoice.total_amount?.toFixed(2)) || '0.00'}
                  </td>
                  <td className="border border-gray-300 p-2 text-red-600">
                    {invoice.discount && invoice.discount > 0 ? (
                      <div>
                        <span>{currency} {invoice.discount.toFixed(2)}</span>
                        {invoice.discount_type === 'percentage' && invoice.discount_value && (
                          <small className="block text-xs">(%{invoice.discount_value})</small>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">لا يوجد</span>
                    )}
                  </td>
                  <td className="border border-gray-300 p-2 font-semibold text-green-600">
                    {currency} {(invoice.total_after_discount || invoice.total_amount)?.toFixed(2) || '0.00'}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <span className={`px-2 py-1 rounded text-sm cursor-pointer ${invoice.status === 'مدفوعة' ? 'bg-green-100 text-green-800' :
                      invoice.status === 'غير مدفوعة' ? 'bg-red-100 text-red-800' :
                        invoice.status === 'مدفوعة جزئياً' ? 'bg-yellow-100 text-yellow-800' :
                          invoice.status === 'انتظار' ? 'bg-blue-100 text-blue-800' :
                            invoice.status === 'تم التنفيذ' ? 'bg-green-100 text-green-800' :
                              invoice.status === 'تم التصنيع' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                      }`}>
                      {invoice.status === 'مدفوعة' && invoice.payment_method === 'آجل'
                        ? (invoice.status_description || `تم الدفع ${invoice.payment_method_used || 'نقدي'}`)
                        : invoice.status === 'مدفوعة جزئياً' && invoice.payment_method === 'آجل'
                          ? (invoice.status_description || invoice.status)
                          : invoice.status}
                    </span>
                  </td>

                  <td className="border border-gray-300 p-2">
                    <div className="flex flex-wrap gap-1">
                      <button
                        onClick={() => printInvoice(invoice)}
                        className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                      >
                        طباعة
                      </button>
                      <button
                        onClick={() => startEditInvoice(invoice)}
                        className="bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600"
                      >
                        تعديل
                      </button>
                      <button
                        onClick={() => changePaymentMethod(invoice.id)}
                        className="bg-purple-500 text-white px-2 py-1 rounded text-sm hover:bg-purple-600"
                        title="تغيير طريقة الدفع"
                      >
                        💳 تحويل
                      </button>
                      <button
                        onClick={() => cancelInvoice(invoice.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                        title="إلغاء الفاتورة وإرجاع المواد"
                      >
                        ❌ إلغاء
                      </button>
                      {invoice.status === 'انتظار' && (
                        <button
                          onClick={() => updateInvoiceStatus(invoice.id, 'تم التنفيذ')}
                          className="bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600"
                        >
                          تم التنفيذ
                        </button>
                      )}
                      <button
                        onClick={() => fetchEditHistory(invoice.id)}
                        className="bg-orange-500 text-white px-2 py-1 rounded text-sm hover:bg-orange-600"
                        title="سجل التعديلات"
                      >
                        📜 سجل
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredInvoices.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              لا توجد فواتير تطابق معايير البحث
            </div>
          )}
        </div>
      </div>

      {/* Edit Invoice Modal */}
      {editingInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-4xl max-h-screen overflow-y-auto" dir="rtl">
            <h3 className="text-xl font-semibold mb-4">تعديل الفاتورة</h3>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-1">عنوان الفاتورة</label>
                <input
                  type="text"
                  value={editForm.invoice_title}
                  onChange={(e) => setEditForm({ ...editForm, invoice_title: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="عنوان الفاتورة (اختياري)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">اسم المشرف</label>
                <input
                  type="text"
                  value={editForm.supervisor_name}
                  onChange={(e) => setEditForm({ ...editForm, supervisor_name: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="اسم المشرف (اختياري)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">اسم العميل</label>
                <input
                  type="text"
                  value={editForm.customer_name}
                  onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="اسم العميل"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">طريقة الدفع</label>
                <select
                  value={editForm.payment_method}
                  onChange={(e) => setEditForm({ ...editForm, payment_method: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="نقدي">نقدي</option>
                  <option value="فودافون 010">فودافون 010</option>
                  <option value="كاش 0100">كاش 0100</option>
                  <option value="آجل">آجل</option>
                  <option value="انستا باي">انستا باي</option>
                  <option value="Yad_Elsawy">Yad Elsawy</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">نوع الخصم</label>
                <select
                  value={editForm.discount_type}
                  onChange={(e) => setEditForm({ ...editForm, discount_type: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="amount">مبلغ ثابت</option>
                  <option value="percentage">نسبة مئوية</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">قيمة الخصم</label>
                <input
                  type="number"
                  step="0.01"
                  value={editForm.discount_value}
                  onChange={(e) => setEditForm({ ...editForm, discount_value: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder={editForm.discount_type === 'percentage' ? '0-100' : '0.00'}
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">ملاحظات</label>
              <textarea
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded"
                rows="3"
                placeholder="ملاحظات إضافية (اختياري)"
              />
            </div>

            {/* Items Display with Edit capability */}
            <div className="mb-4">
              <h4 className="text-lg font-medium mb-2">عناصر الفاتورة</h4>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 p-2">المنتج</th>
                      <th className="border border-gray-300 p-2">الكمية</th>
                      <th className="border border-gray-300 p-2">سعر الوحدة</th>
                      <th className="border border-gray-300 p-2">الإجمالي</th>
                      <th className="border border-gray-300 p-2">إجراءات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {editForm.items.map((item, index) => (
                      <tr key={index}>
                        <td className="border border-gray-300 p-2">
                          {item.product_type === 'local' || item.local_product_details ? (
                            <input
                              type="text"
                              value={item.product_name || `${item.local_product_details?.product_size || ''} - ${item.local_product_details?.product_type || ''}`}
                              onChange={(e) => {
                                const newItems = [...editForm.items];
                                newItems[index].product_name = e.target.value;
                                setEditForm({ ...editForm, items: newItems });
                              }}
                              className="w-full p-1 border border-gray-300 rounded"
                              placeholder="مقاس المنتج - نوع المنتج"
                            />
                          ) : (
                            <div className="space-y-1">
                              {/* Seal Type */}
                              <div className="flex items-center space-x-2 space-x-reverse">
                                <label className="text-xs font-medium w-16">نوع السيل:</label>
                                <select
                                  value={item.seal_type || ''}
                                  onChange={(e) => {
                                    const newItems = [...editForm.items];
                                    newItems[index].seal_type = e.target.value;
                                    setEditForm({ ...editForm, items: newItems });
                                  }}
                                  className="flex-1 p-1 text-xs border border-gray-300 rounded"
                                >
                                  <option value="">اختر النوع</option>
                                  <option value="RSL">RSL</option>
                                  <option value="RS">RS</option>
                                  <option value="RSS">RSS</option>
                                  <option value="RSE">RSE</option>
                                  <option value="B17">B17</option>
                                  <option value="B3">B3</option>
                                  <option value="B14">B14</option>
                                  <option value="B1">B1</option>
                                  <option value="R15">R15</option>
                                  <option value="R17">R17</option>
                                  <option value="W1">W1</option>
                                  <option value="W4">W4</option>
                                  <option value="W5">W5</option>
                                  <option value="W11">W11</option>
                                  <option value="WBT">WBT</option>
                                  <option value="XR">XR</option>
                                  <option value="CH">CH</option>
                                  <option value="VR">VR</option>
                                </select>
                              </div>

                              {/* Material Type */}
                              <div className="flex items-center space-x-2 space-x-reverse">
                                <label className="text-xs font-medium w-16">نوع الخامة:</label>
                                <select
                                  value={item.material_type || ''}
                                  onChange={(e) => {
                                    const newItems = [...editForm.items];
                                    newItems[index].material_type = e.target.value;
                                    setEditForm({ ...editForm, items: newItems });
                                  }}
                                  className="flex-1 p-1 text-xs border border-gray-300 rounded"
                                >
                                  <option value="">اختر الخامة</option>
                                  <option value="NBR">NBR</option>
                                  <option value="BUR">BUR</option>
                                  <option value="BT">BT</option>
                                  <option value="VT">VT</option>
                                  <option value="BOOM">BOOM</option>
                                </select>
                              </div>

                              {/* Dimensions */}
                              <div className="flex items-center space-x-1 space-x-reverse">
                                <input
                                  type="number"
                                  step="0.1"
                                  value={item.inner_diameter || ''}
                                  onChange={(e) => {
                                    const newItems = [...editForm.items];
                                    newItems[index].inner_diameter = parseFloat(e.target.value) || 0;
                                    setEditForm({ ...editForm, items: newItems });
                                  }}
                                  placeholder="داخلي"
                                  className="w-12 p-1 text-xs border border-gray-300 rounded"
                                />
                                <span className="text-xs">×</span>
                                <input
                                  type="number"
                                  step="0.1"
                                  value={item.outer_diameter || ''}
                                  onChange={(e) => {
                                    const newItems = [...editForm.items];
                                    newItems[index].outer_diameter = parseFloat(e.target.value) || 0;
                                    setEditForm({ ...editForm, items: newItems });
                                  }}
                                  placeholder="خارجي"
                                  className="w-12 p-1 text-xs border border-gray-300 rounded"
                                />
                                <span className="text-xs">×</span>
                                <input
                                  type="number"
                                  step="0.1"
                                  value={item.height || ''}
                                  onChange={(e) => {
                                    const newItems = [...editForm.items];
                                    newItems[index].height = parseFloat(e.target.value) || 0;
                                    setEditForm({ ...editForm, items: newItems });
                                  }}
                                  placeholder="ارتفاع"
                                  className="w-12 p-1 text-xs border border-gray-300 rounded"
                                />
                              </div>
                            </div>
                          )}
                        </td>
                        <td className="border border-gray-300 p-2">
                          <input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => {
                              const newItems = [...editForm.items];
                              newItems[index].quantity = parseInt(e.target.value) || 0;
                              newItems[index].total_price = newItems[index].unit_price * newItems[index].quantity;
                              setEditForm({ ...editForm, items: newItems });
                            }}
                            className="w-full p-1 border border-gray-300 rounded"
                          />
                        </td>
                        <td className="border border-gray-300 p-2">
                          <input
                            type="number"
                            step="0.01"
                            value={item.unit_price}
                            onChange={(e) => {
                              const newItems = [...editForm.items];
                              newItems[index].unit_price = parseFloat(e.target.value) || 0;
                              newItems[index].total_price = newItems[index].unit_price * newItems[index].quantity;
                              setEditForm({ ...editForm, items: newItems });
                            }}
                            className="w-full p-1 border border-gray-300 rounded"
                          />
                        </td>
                        <td className="border border-gray-300 p-2 font-semibold">
                          {currency} {(item.total_price || 0).toFixed(2)}
                        </td>
                        <td className="border border-gray-300 p-2">
                          <button
                            onClick={() => {
                              const newItems = editForm.items.filter((_, i) => i !== index);
                              setEditForm({ ...editForm, items: newItems });
                            }}
                            className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                          >
                            حذف
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add Product Button */}
              <button
                onClick={() => {
                  // Add a new empty item for editing
                  const newItem = {
                    seal_type: '',
                    material_type: '',
                    inner_diameter: '',
                    outer_diameter: '',
                    height: '',
                    quantity: 1,
                    unit_price: 0,
                    total_price: 0
                  };
                  setEditForm({
                    ...editForm,
                    items: [...editForm.items, newItem]
                  });
                }}
                className="mt-2 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                إضافة منتج جديد
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 space-x-reverse">
              <button
                onClick={cancelEdit}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
              <button
                onClick={saveInvoiceEdit}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                حفظ التعديلات
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Password Modal for Invoice Operations */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" dir="rtl">
          <div className="bg-white rounded-lg p-8 max-w-md w-full shadow-2xl">
            <h3 className="text-2xl font-bold mb-4 text-blue-600">
              🔐 تأكيد العملية
            </h3>

            <div className="mb-4 p-4 bg-blue-50 border-r-4 border-blue-500 rounded">
              <p className="text-sm text-gray-700">
                {pendingOperation?.type === 'cancel' && '❌ إلغاء الفاتورة'}
                {pendingOperation?.type === 'edit' && '✏️ تعديل الفاتورة'}
                {pendingOperation?.type === 'changePayment' && '💳 تحويل طريقة الدفع'}
              </p>
              <p className="text-xs text-gray-600 mt-2">
                يتطلب كلمة المرور للمتابعة
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                كلمة المرور (1462):
              </label>
              <input
                type="password"
                value={operationPassword}
                onChange={(e) => setOperationPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && executeOperation()}
                placeholder="أدخل كلمة المرور"
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                autoFocus
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={executeOperation}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors"
              >
                ✅ تأكيد
              </button>
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  setPendingOperation(null);
                  setOperationPassword('');
                }}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-3 rounded-lg font-semibold transition-colors"
              >
                ❌ إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
          onClick={() => setShowHistoryModal(false)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()} dir="rtl">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">📜 سجل تعديلات الفاتورة</h3>
                <button
                  onClick={() => setShowHistoryModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              {historyLoading ? (
                <div className="text-center py-8 text-gray-500">⏳ جاري التحميل...</div>
              ) : editHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  لا توجد تعديلات سابقة على هذه الفاتورة
                </div>
              ) : (
                <div className="space-y-3">
                  {editHistory.map((entry, index) => (
                    <div key={entry.id || index}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm font-medium text-gray-800">
                            📅 {new Date(entry.edited_at).toLocaleString('ar-EG')}
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            👤 بواسطة: {entry.edited_by || 'غير محدد'}
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            التغييرات: {entry.changes_summary}
                          </div>
                        </div>
                        <button
                          onClick={() => revertToVersion(entry.id)}
                          className="bg-yellow-500 text-white px-3 py-1 rounded text-sm hover:bg-yellow-600 flex-shrink-0"
                        >
                          ↩️ تراجع
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Deleted Invoices Component
const DeletedInvoices = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [deletedInvoices, setDeletedInvoices] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Invoice operations password change states
  const [showInvoiceOpsPasswordChange, setShowInvoiceOpsPasswordChange] = useState(false);
  const [invoiceOpsOldPassword, setInvoiceOpsOldPassword] = useState('');
  const [invoiceOpsNewPassword, setInvoiceOpsNewPassword] = useState('');

  // Verify password
  const verifyPassword = async () => {
    try {
      const response = await axios.post(`${API}/deleted-invoices/verify-password`, {
        password: password
      });

      if (response.data.success) {
        setIsAuthenticated(true);
        fetchDeletedInvoices();
      } else {
        alert('كلمة المرور غير صحيحة');
        setPassword('');
      }
    } catch (error) {
      console.error('Error verifying password:', error);
      alert('حدث خطأ في التحقق من كلمة المرور');
    }
  };

  // Change password
  const changePassword = async () => {
    if (!oldPassword || !newPassword) {
      alert('الرجاء إدخال كلمة المرور القديمة والجديدة');
      return;
    }

    if (newPassword.length < 4) {
      alert('كلمة المرور يجب أن تكون 4 أرقام على الأقل');
      return;
    }

    try {
      await axios.post(`${API}/deleted-invoices/change-password`, {
        old_password: oldPassword,
        new_password: newPassword
      });

      alert('تم تغيير كلمة المرور بنجاح');
      setShowPasswordChange(false);
      setOldPassword('');
      setNewPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في تغيير كلمة المرور');
    }
  };

  // Change invoice operations password (1462)
  const changeInvoiceOpsPassword = async () => {
    if (!invoiceOpsOldPassword || !invoiceOpsNewPassword) {
      alert('الرجاء إدخال كلمة المرور القديمة والجديدة');
      return;
    }

    if (invoiceOpsNewPassword.length < 4) {
      alert('كلمة المرور يجب أن تكون 4 أرقام على الأقل');
      return;
    }

    try {
      await axios.post(`${API}/invoice-operations/change-password`, {
        old_password: invoiceOpsOldPassword,
        new_password: invoiceOpsNewPassword
      });

      alert('تم تغيير كلمة مرور العمليات (إلغاء/تعديل/تحويل) بنجاح');
      setShowInvoiceOpsPasswordChange(false);
      setInvoiceOpsOldPassword('');
      setInvoiceOpsNewPassword('');
    } catch (error) {
      console.error('Error changing invoice ops password:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في تغيير كلمة المرور');
    }
  };

  const fetchDeletedInvoices = async () => {
    try {
      const response = await axios.get(`${API}/deleted-invoices`);
      setDeletedInvoices(response.data || []);
    } catch (error) {
      console.error('Error fetching deleted invoices:', error);
      alert('حدث خطأ في جلب الفواتير المحذوفة');
    }
  };

  const handleRestore = async (invoiceId, invoiceNumber) => {
    if (!confirm(`هل أنت متأكد من استعادة الفاتورة ${invoiceNumber}؟\n\nملاحظة: سيتم استعادة الفاتورة فقط، لن يتم استرجاع المواد أو الخزينة تلقائياً`)) {
      return;
    }

    try {
      const response = await axios.post(`${API}/deleted-invoices/${invoiceId}/restore`, null, {
        params: { username: user?.username }
      });
      alert(response.data.message + '\n\n' + (response.data.warning || ''));
      fetchDeletedInvoices();
    } catch (error) {
      console.error('Error restoring invoice:', error);
      alert('حدث خطأ في استعادة الفاتورة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePermanentDelete = async (invoiceId, invoiceNumber) => {
    if (!confirm(`⚠️ تحذير: هل أنت متأكد من حذف الفاتورة ${invoiceNumber} نهائياً؟\n\nهذا الإجراء لا يمكن التراجع عنه!`)) {
      return;
    }

    try {
      await axios.delete(`${API}/deleted-invoices/${invoiceId}`);
      alert('تم حذف الفاتورة نهائياً');
      fetchDeletedInvoices();
    } catch (error) {
      console.error('Error deleting invoice:', error);
      alert('حدث خطأ في حذف الفاتورة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const filteredInvoices = deletedInvoices.filter(invoice => {
    const searchLower = searchTerm.toLowerCase();
    return (
      invoice.invoice_number?.toLowerCase().includes(searchLower) ||
      invoice.customer_name?.toLowerCase().includes(searchLower) ||
      invoice.payment_method?.toLowerCase().includes(searchLower)
    );
  });

  // If not authenticated, show password screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-500 to-orange-600 p-6" dir="rtl">
        <div className="bg-white p-8 rounded-lg shadow-2xl max-w-md w-full">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🗑️</div>
            <h2 className="text-2xl font-bold text-gray-800">الفواتير المحذوفة</h2>
            <p className="text-gray-600 mt-2">الرجاء إدخال كلمة المرور للدخول</p>
          </div>

          <div className="space-y-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && verifyPassword()}
              placeholder="كلمة المرور"
              className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-red-500 focus:outline-none text-center text-lg"
              autoFocus
            />

            <button
              onClick={verifyPassword}
              className="w-full bg-red-500 text-white py-3 rounded-lg hover:bg-red-600 font-semibold text-lg transition-colors"
            >
              دخول
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main deleted invoices interface
  return (
    <div className="p-6 bg-gray-50 min-h-screen" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">🗑️ الفواتير المحذوفة</h1>
          <p className="text-gray-600 mt-1">إدارة واستعادة الفواتير المحذوفة</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPasswordChange(!showPasswordChange)}
            className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            title="تغيير كلمة مرور الصفحة"
          >
            🔑 الصفحة
          </button>
          <button
            onClick={() => setShowInvoiceOpsPasswordChange(!showInvoiceOpsPasswordChange)}
            className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
            title="تغيير كلمة مرور العمليات"
          >
            🔐 العمليات
          </button>
          <button
            onClick={fetchDeletedInvoices}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            🔄 تحديث
          </button>
        </div>
      </div>

      {/* Password Change Section */}
      {showPasswordChange && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            🔑 تغيير كلمة المرور
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                كلمة المرور القديمة
              </label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                كلمة المرور الجديدة
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex items-end gap-2">
              <button
                onClick={changePassword}
                className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 font-semibold"
              >
                ✅ تأكيد
              </button>
              <button
                onClick={() => {
                  setShowPasswordChange(false);
                  setOldPassword('');
                  setNewPassword('');
                }}
                className="flex-1 bg-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-400 font-semibold"
              >
                ❌ إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Invoice Operations Password Change Section */}
      {showInvoiceOpsPasswordChange && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            🔐 تغيير كلمة مرور عمليات الفواتير
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            تغيير كلمة المرور المستخدمة في: <strong>إلغاء الفواتير، تعديل الفواتير، تحويل طريقة الدفع</strong>
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                كلمة المرور القديمة (1462)
              </label>
              <input
                type="password"
                value={invoiceOpsOldPassword}
                onChange={(e) => setInvoiceOpsOldPassword(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                كلمة المرور الجديدة
              </label>
              <input
                type="password"
                value={invoiceOpsNewPassword}
                onChange={(e) => setInvoiceOpsNewPassword(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div className="flex items-end gap-2">
              <button
                onClick={changeInvoiceOpsPassword}
                className="flex-1 bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-600 font-semibold"
              >
                ✅ تأكيد
              </button>
              <button
                onClick={() => {
                  setShowInvoiceOpsPasswordChange(false);
                  setInvoiceOpsOldPassword('');
                  setInvoiceOpsNewPassword('');
                }}
                className="flex-1 bg-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-400 font-semibold"
              >
                ❌ إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="البحث (رقم الفاتورة، اسم العميل، طريقة الدفع...)"
          className="w-full p-2 border border-gray-300 rounded"
        />
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-lg shadow-md overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-300 p-2">رقم الفاتورة</th>
              <th className="border border-gray-300 p-2">التاريخ</th>
              <th className="border border-gray-300 p-2">العميل</th>
              <th className="border border-gray-300 p-2">الإجمالي</th>
              <th className="border border-gray-300 p-2">طريقة الدفع</th>
              <th className="border border-gray-300 p-2">تاريخ الحذف</th>
              <th className="border border-gray-300 p-2">الإجراءات</th>
            </tr>
          </thead>
          <tbody>
            {filteredInvoices.length === 0 ? (
              <tr>
                <td colSpan="7" className="border border-gray-300 p-4 text-center text-gray-500">
                  لا توجد فواتير محذوفة
                </td>
              </tr>
            ) : (
              filteredInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="border border-gray-300 p-2 font-medium">
                    {invoice.invoice_number}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {new Date(invoice.created_at).toLocaleDateString('ar-EG')}
                  </td>
                  <td className="border border-gray-300 p-2">{invoice.customer_name}</td>
                  <td className="border border-gray-300 p-2 font-bold">
                    {invoice.total_amount?.toFixed(2)} {currency}
                  </td>
                  <td className="border border-gray-300 p-2">{invoice.payment_method}</td>
                  <td className="border border-gray-300 p-2 text-sm text-gray-600">
                    {new Date(invoice.deleted_at).toLocaleDateString('ar-EG', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse justify-center">
                      <button
                        onClick={() => handleRestore(invoice.id, invoice.invoice_number)}
                        className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                      >
                        ↩️ استعادة
                      </button>
                      <button
                        onClick={() => handlePermanentDelete(invoice.id, invoice.invoice_number)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        🗑️ حذف نهائي
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <strong>إجمالي الفواتير المحذوفة:</strong> {filteredInvoices.length}
        </p>
        <p className="text-xs text-gray-600 mt-2">
          💡 <strong>ملاحظة:</strong> استعادة الفاتورة سترجعها إلى قائمة الفواتير النشطة، لكن لن يتم استرجاع المواد أو الخزينة تلقائياً.
        </p>
      </div>
    </div>
  );
};

// Customer Statement Component (كشف الحساب)
const CustomerStatement = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [statement, setStatement] = useState(null);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      // Sort customers alphabetically by name
      const sortedCustomers = (response.data || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'ar')
      );
      setCustomers(sortedCustomers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchStatement = async () => {
    if (!selectedCustomer) {
      alert('الرجاء اختيار عميل');
      return;
    }

    setLoading(true);
    try {
      const params = {};
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;

      const response = await axios.get(`${API}/customer-statement/${selectedCustomer}`, { params });
      setStatement(response.data);
    } catch (error) {
      console.error('Error fetching statement:', error);
      alert('حدث خطأ في جلب كشف الحساب: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const printStatement = () => {
    if (!statement) return;

    const printWindow = window.open('', '', 'width=800,height=600');
    const customer = statement.customer;
    const transactions = statement.transactions || [];
    const summary = statement.summary || {};

    printWindow.document.write(`
      <!DOCTYPE html>
      <html dir="rtl">
      <head>
        <title>كشف حساب - ${customer.name}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 20px;
            direction: rtl;
          }
          .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
          }
          .info-section {
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
          }
          .info-box {
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            width: 45%;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
          }
          th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
          }
          th {
            background-color: #f2f2f2;
            font-weight: bold;
          }
          .summary {
            margin-top: 20px;
            border-top: 2px solid #333;
            padding-top: 10px;
          }
          .summary-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 14px;
          }
          .final-balance {
            font-size: 18px;
            font-weight: bold;
            color: ${summary.final_balance >= 0 ? 'green' : 'red'};
          }
          @media print {
            body { padding: 10px; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>كشف حساب عام</h1>
          <p>مرتب بتواريخ القيود</p>
        </div>

        <div class="info-section">
          <div class="info-box">
            <p><strong>اسم الحساب:</strong> ${customer.name}</p>
            <p><strong>رقم الهاتف:</strong> ${customer.phone || 'غير محدد'}</p>
            ${customer.is_also_supplier ? '<p><strong>ملاحظة:</strong> هذا العميل مورد أيضاً</p>' : ''}
          </div>
          <div class="info-box">
            <p><strong>من تاريخ:</strong> ${statement.period.from_date}</p>
            <p><strong>إلى تاريخ:</strong> ${statement.period.to_date}</p>
            <p><strong>تاريخ الطباعة:</strong> ${new Date().toLocaleDateString('ar-EG')}</p>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>التاريخ</th>
              <th>نوع القيد</th>
              <th>البيان</th>
              <th>مدين</th>
              <th>دائن</th>
              <th>الرصيد</th>
            </tr>
          </thead>
          <tbody>
            ${transactions.map(t => `
              <tr>
                <td>${new Date(t.date).toLocaleDateString('ar-EG')}</td>
                <td>${t.type}</td>
                <td>${t.description}</td>
                <td>${t.debit > 0 ? t.debit.toFixed(2) : '-'}</td>
                <td>${t.credit > 0 ? t.credit.toFixed(2) : '-'}</td>
                <td>${t.balance.toFixed(2)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="summary">
          <div class="summary-row">
            <span><strong>إجمالي الدائن:</strong></span>
            <span>${summary.total_credit?.toFixed(2) || '0.00'} ${currency}</span>
          </div>
          <div class="summary-row">
            <span><strong>إجمالي المدين:</strong></span>
            <span>${summary.total_debit?.toFixed(2) || '0.00'} ${currency}</span>
          </div>
          <div class="summary-row final-balance">
            <span><strong>الرصيد النهائي:</strong></span>
            <span>${summary.final_balance?.toFixed(2) || '0.00'} ${currency}</span>
          </div>
        </div>

        <p style="margin-top: 30px; text-align: left;">المحاسب يعتمد،،،</p>
      </body>
      </html>
    `);

    printWindow.document.close();
    printWindow.print();
  };

  return (
    <div className="p-6" dir="rtl">
      <h1 className="text-3xl font-bold mb-6">كشف حساب العملاء</h1>

      {/* Customer Selection and Filters */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">اختر العميل *</label>
            <select
              value={selectedCustomer}
              onChange={(e) => setSelectedCustomer(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="">-- اختر عميل --</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">من تاريخ</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">إلى تاريخ</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchStatement}
              disabled={loading || !selectedCustomer}
              className={`w-full px-4 py-2 rounded text-white ${loading || !selectedCustomer
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600'
                }`}
            >
              {loading ? '⏳ جاري التحميل...' : '📋 عرض كشف الحساب'}
            </button>
          </div>
        </div>
      </div>

      {/* Statement Display */}
      {statement && (
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6 pb-4 border-b-2">
            <div>
              <h2 className="text-2xl font-bold">كشف حساب عام</h2>
              <p className="text-sm text-gray-600">مرتب بتواريخ القيود</p>
            </div>
            <button
              onClick={printStatement}
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
            >
              🖨️ طباعة
            </button>
          </div>

          {/* Customer Info */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded">
              <p className="mb-2"><strong>اسم الحساب:</strong> {statement.customer.name}</p>
              <p className="mb-2"><strong>رقم الهاتف:</strong> {statement.customer.phone || 'غير محدد'}</p>
              {statement.customer.is_also_supplier && (
                <p className="text-orange-600 font-medium">⚠️ هذا العميل مورد أيضاً</p>
              )}
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="mb-2"><strong>من تاريخ:</strong> {statement.period.from_date}</p>
              <p className="mb-2"><strong>إلى تاريخ:</strong> {statement.period.to_date}</p>
              <p className="mb-2"><strong>التاريخ:</strong> {new Date().toLocaleDateString('ar-EG')}</p>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="overflow-x-auto mb-6">
            <table className="min-w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">التاريخ</th>
                  <th className="border border-gray-300 p-2">نوع القيد</th>
                  <th className="border border-gray-300 p-2">البيان</th>
                  <th className="border border-gray-300 p-2">المرجع</th>
                  <th className="border border-gray-300 p-2">مدين</th>
                  <th className="border border-gray-300 p-2">دائن</th>
                  <th className="border border-gray-300 p-2">الرصيد</th>
                </tr>
              </thead>
              <tbody>
                {statement.transactions.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="border border-gray-300 p-4 text-center text-gray-500">
                      لا توجد معاملات في هذه الفترة
                    </td>
                  </tr>
                ) : (
                  statement.transactions.map((trans, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="border border-gray-300 p-2">
                        {new Date(trans.date).toLocaleDateString('ar-EG')}
                      </td>
                      <td className="border border-gray-300 p-2">{trans.type}</td>
                      <td className="border border-gray-300 p-2 text-right">{trans.description}</td>
                      <td className="border border-gray-300 p-2">{trans.reference}</td>
                      <td className="border border-gray-300 p-2 text-red-600 font-medium">
                        {trans.debit > 0 ? trans.debit.toFixed(2) : '-'}
                      </td>
                      <td className="border border-gray-300 p-2 text-green-600 font-medium">
                        {trans.credit > 0 ? trans.credit.toFixed(2) : '-'}
                      </td>
                      <td className="border border-gray-300 p-2 font-bold">
                        {trans.balance.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg border-t-4 border-blue-500">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">إجمالي الدائن</p>
                <p className="text-2xl font-bold text-green-600">
                  {statement.summary.total_credit?.toFixed(2)} {currency}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">إجمالي المدين</p>
                <p className="text-2xl font-bold text-red-600">
                  {statement.summary.total_debit?.toFixed(2)} {currency}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">الرصيد النهائي</p>
                <p className={`text-3xl font-bold ${statement.summary.final_balance >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                  {statement.summary.final_balance?.toFixed(2)} {currency}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!statement && (
        <div className="bg-blue-50 p-6 rounded-lg border-r-4 border-blue-500">
          <h3 className="font-bold mb-2">📝 تعليمات:</h3>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li>اختر العميل المطلوب من القائمة</li>
            <li>يمكنك تحديد فترة زمنية معينة (اختياري)</li>
            <li>اضغط على "عرض كشف الحساب" لعرض التقرير</li>
            <li>يمكنك طباعة كشف الحساب بالضغط على زر الطباعة</li>
            <li><strong>ملاحظة:</strong> الفواتير = دائن (موجب) | الدفعات والمشتريات = مدين (سالب)</li>
          </ul>
        </div>
      )}
    </div>
  );
};

// Customer Account Settlement Component - تصفية حساب العميل
const SettleAccount = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [deferredInvoices, setDeferredInvoices] = useState([]);
  const [amountPaid, setAmountPaid] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('نقدي');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [isCustomerAlsoSupplier, setIsCustomerAlsoSupplier] = useState(false);
  const [supplierBalance, setSupplierBalance] = useState(0);

  useEffect(() => {
    fetchCustomers();
    fetchSuppliers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      const sortedCustomers = (response.data || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'ar')
      );
      setCustomers(sortedCustomers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/suppliers`);
      setSuppliers(response.data || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    }
  };

  const fetchCustomerInvoices = async (customerId) => {
    try {
      const response = await axios.get(`${API}/invoices`);
      const customer = customers.find(c => c.id === customerId);

      if (customer) {
        const customerInvoices = response.data.filter(inv =>
          inv.customer_name === customer.name &&
          inv.payment_method === 'آجل' &&
          inv.remaining_amount > 0
        ).sort((a, b) => new Date(a.date) - new Date(b.date)); // Sort by date ascending

        setDeferredInvoices(customerInvoices);
      }
    } catch (error) {
      console.error('Error fetching invoices:', error);
    }
  };

  const handleCustomerChange = (customerId) => {
    setSelectedCustomer(customerId);
    setResult(null);
    if (customerId) {
      fetchCustomerInvoices(customerId);

      // Check if customer is also supplier
      const customer = customers.find(c => c.id === customerId);

      if (customer) {
        const supplier = suppliers.find(s => s.name === customer.name);

        if (supplier) {
          // Support both 'balance' and 'current_balance' fields
          const balance = supplier.current_balance !== undefined
            ? supplier.current_balance
            : (supplier.balance || 0);

          if (balance > 0) {
            setIsCustomerAlsoSupplier(true);
            setSupplierBalance(balance);
          } else {
            setIsCustomerAlsoSupplier(false);
            setSupplierBalance(0);
          }
        } else {
          setIsCustomerAlsoSupplier(false);
          setSupplierBalance(0);
        }
      }
    } else {
      setDeferredInvoices([]);
      setIsCustomerAlsoSupplier(false);
      setSupplierBalance(0);
    }
  };

  const handleSettleAccount = async () => {
    if (!selectedCustomer) {
      alert('الرجاء اختيار العميل');
      return;
    }

    if (!amountPaid || parseFloat(amountPaid) <= 0) {
      alert('الرجاء إدخال مبلغ صحيح');
      return;
    }

    if (!confirm(`هل أنت متأكد من تصفية حساب العميل بمبلغ ${parseFloat(amountPaid).toFixed(2)} ${currency}؟\n\nسيتم توزيع المبلغ على الفواتير الآجلة من الأقدم للأحدث`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/customers/${selectedCustomer}/settle-account`,
        null,
        {
          params: {
            amount_paid: parseFloat(amountPaid),
            payment_method: paymentMethod,
            username: user?.username
          }
        }
      );

      setResult(response.data);
      setAmountPaid('');

      // Refresh invoices
      fetchCustomerInvoices(selectedCustomer);

      // Show detailed result
      let message = `✅ ${response.data.message}\n\n`;
      message += `💰 المبلغ المدفوع: ${response.data.total_amount_paid.toFixed(2)} ${currency}\n`;
      message += `📊 تم توزيع: ${response.data.amount_distributed.toFixed(2)} ${currency}\n`;

      if (response.data.remaining_amount > 0) {
        message += `💵 متبقي: ${response.data.remaining_amount.toFixed(2)} ${currency}\n\n`;
      }

      message += `📋 الفواتير المدفوعة (${response.data.invoices_count}):\n`;
      response.data.paid_invoices.forEach(inv => {
        message += `\n• ${inv.invoice_number}\n`;
        message += `  المدفوع: ${inv.amount_paid.toFixed(2)} ${currency}\n`;
        message += `  الحالة: ${inv.status}\n`;
      });

      alert(message);

    } catch (error) {
      console.error('Error settling account:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في تصفية الحساب');
    } finally {
      setLoading(false);
    }
  };

  // Reconcile customer-supplier account
  const handleReconciliation = async () => {
    if (!selectedCustomer) {
      alert('الرجاء اختيار العميل');
      return;
    }

    const settlementAmount = Math.min(supplierBalance, totalRemaining);

    const confirmMessage = `🔄 تسوية الحساب\n\n` +
      `العميل/المورد: ${customers.find(c => c.id === selectedCustomer)?.name}\n\n` +
      `رصيد المورد: ${supplierBalance.toFixed(2)} ${currency}\n` +
      `ديون العميل: ${totalRemaining.toFixed(2)} ${currency}\n\n` +
      `سيتم تسوية: ${settlementAmount.toFixed(2)} ${currency}\n\n` +
      `بعد التسوية:\n` +
      `• رصيد المورد: ${(supplierBalance - settlementAmount).toFixed(2)} ${currency}\n` +
      `• ديون العميل: ${(totalRemaining - settlementAmount).toFixed(2)} ${currency}\n\n` +
      `⚠️ ملاحظة: تسوية داخلية بدون تأثير على الخزينة\n\n` +
      `هل تريد المتابعة؟`;

    if (!confirm(confirmMessage)) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/customers/${selectedCustomer}/reconcile-with-supplier`,
        null,
        {
          params: {
            username: user?.username
          }
        }
      );

      // Refresh data
      fetchCustomerInvoices(selectedCustomer);
      fetchSuppliers();

      // Show detailed result
      let message = `✅ ${response.data.message}\n\n`;
      message += `📊 التفاصيل:\n`;
      message += `• رصيد المورد السابق: ${response.data.supplier_previous_balance.toFixed(2)} ${currency}\n`;
      message += `• ديون العميل السابقة: ${response.data.customer_previous_debt.toFixed(2)} ${currency}\n`;
      message += `• مبلغ التسوية: ${response.data.settlement_amount.toFixed(2)} ${currency}\n\n`;
      message += `📉 بعد التسوية:\n`;
      message += `• رصيد المورد الجديد: ${response.data.supplier_new_balance.toFixed(2)} ${currency}\n`;
      message += `• ديون العميل المتبقية: ${response.data.customer_remaining_debt.toFixed(2)} ${currency}\n\n`;
      message += `📋 الفواتير المسواة (${response.data.invoices_count}):\n`;
      response.data.settled_invoices.forEach(inv => {
        message += `\n• ${inv.invoice_number}\n`;
        message += `  المدفوع: ${inv.amount_paid.toFixed(2)} ${currency}\n`;
        message += `  الحالة: ${inv.status}\n`;
      });
      message += `\n${response.data.note}`;

      alert(message);

      // Update local state
      setIsCustomerAlsoSupplier(response.data.supplier_new_balance > 0);
      setSupplierBalance(response.data.supplier_new_balance);

    } catch (error) {
      console.error('Error reconciling account:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في التسوية');
    } finally {
      setLoading(false);
    }
  };

  const totalRemaining = deferredInvoices.reduce((sum, inv) => sum + inv.remaining_amount, 0);

  return (
    <div className="p-6 bg-gray-50 min-h-screen" dir="rtl">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
          💵 تصفية حساب العميل
        </h1>
        <p className="text-gray-600 mt-2">دفع مبلغ لتصفية فواتير العميل الآجلة</p>
      </div>

      {/* Settlement Form */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-xl font-semibold mb-4">بيانات التصفية</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Customer Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              اختر العميل *
            </label>
            <select
              value={selectedCustomer || ''}
              onChange={(e) => handleCustomerChange(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value="">-- اختر العميل --</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </div>

          {/* Amount Paid */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              المبلغ المدفوع ({currency}) *
            </label>
            <input
              type="number"
              step="0.01"
              value={amountPaid}
              onChange={(e) => setAmountPaid(e.target.value)}
              placeholder="0.00"
              className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Payment Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              طريقة الدفع *
            </label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value="نقدي">نقدي</option>
              <option value="فودافون 010">فودافون 010</option>
              <option value="كاش 0100">كاش 0100</option>
              <option value="انستاباي">انستاباي</option>
              <option value="يد الصاوي">يد الصاوي</option>
            </select>
          </div>

          {/* Settle Button */}
          <div className="flex items-end">
            <button
              onClick={handleSettleAccount}
              disabled={loading || !selectedCustomer || !amountPaid}
              className={`w-full py-3 rounded-lg font-semibold text-white transition-colors ${loading || !selectedCustomer || !amountPaid
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-600'
                }`}
            >
              {loading ? '⏳ جاري التصفية...' : '✅ تصفية الحساب'}
            </button>
          </div>
        </div>

        {/* Reconciliation Section - Always visible but disabled if not applicable */}
        {selectedCustomer && (
          <div className={`mt-4 p-4 rounded-lg border-2 transition-all ${isCustomerAlsoSupplier && totalRemaining > 0
            ? 'bg-gradient-to-r from-purple-50 to-blue-50 border-purple-300'
            : 'bg-gray-50 border-gray-300'
            }`}>
            <div className="flex justify-between items-center">
              <div className="flex-1">
                <h4 className={`text-lg font-semibold mb-2 ${isCustomerAlsoSupplier ? 'text-purple-800' : 'text-gray-500'
                  }`}>
                  🔄 تسوية الحساب (عميل ومورد)
                </h4>
                {isCustomerAlsoSupplier ? (
                  <div className="text-sm space-y-1">
                    <p className="text-gray-700">
                      <span className="font-semibold">رصيد المورد:</span> {supplierBalance.toFixed(2)} {currency}
                    </p>
                    <p className="text-gray-700">
                      <span className="font-semibold">ديون العميل:</span> {totalRemaining.toFixed(2)} {currency}
                    </p>
                    <p className="text-purple-700 font-semibold">
                      سيتم تسوية: {Math.min(supplierBalance, totalRemaining).toFixed(2)} {currency}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    {!isCustomerAlsoSupplier && supplierBalance === 0
                      ? '⚠️ العميل ليس مورداً أو رصيد المورد = 0'
                      : totalRemaining === 0
                        ? '⚠️ لا توجد فواتير آجلة مستحقة'
                        : '⚠️ التسوية غير متاحة'}
                  </p>
                )}
              </div>
              <button
                onClick={handleReconciliation}
                disabled={loading || !isCustomerAlsoSupplier || totalRemaining === 0 || supplierBalance === 0}
                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${loading || !isCustomerAlsoSupplier || totalRemaining === 0 || supplierBalance === 0
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-700'
                  }`}
                title={
                  !isCustomerAlsoSupplier
                    ? 'العميل ليس مورداً'
                    : supplierBalance === 0
                      ? 'رصيد المورد = 0'
                      : totalRemaining === 0
                        ? 'لا توجد فواتير آجلة'
                        : 'تسوية الحساب'
                }
              >
                {loading ? '⏳ جاري التسوية...' : '🔄 تسوية'}
              </button>
            </div>
            {isCustomerAlsoSupplier && (
              <p className="text-xs text-purple-600 mt-2">
                ⚠️ تسوية داخلية بدون تأثير على الخزينة
              </p>
            )}
          </div>
        )}
      </div>

      {/* Customer Invoices */}
      {selectedCustomer && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold">
              الفواتير الآجلة ({deferredInvoices.length})
            </h3>
            <div className="text-right">
              <p className="text-sm text-gray-600">إجمالي المستحق</p>
              <p className="text-2xl font-bold text-red-600">
                {totalRemaining.toFixed(2)} {currency}
              </p>
            </div>
          </div>

          {deferredInvoices.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              ✅ لا توجد فواتير آجلة مستحقة لهذا العميل
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 p-3 text-right">رقم الفاتورة</th>
                    <th className="border border-gray-300 p-3 text-right">التاريخ</th>
                    <th className="border border-gray-300 p-3 text-right">الإجمالي</th>
                    <th className="border border-gray-300 p-3 text-right">المدفوع</th>
                    <th className="border border-gray-300 p-3 text-right">المتبقي</th>
                  </tr>
                </thead>
                <tbody>
                  {deferredInvoices.map((invoice, index) => (
                    <tr key={invoice.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="border border-gray-300 p-3 font-semibold">
                        {invoice.invoice_number}
                      </td>
                      <td className="border border-gray-300 p-3">
                        {new Date(invoice.date).toLocaleDateString('ar-EG')}
                      </td>
                      <td className="border border-gray-300 p-3">
                        {invoice.total_amount.toFixed(2)} {currency}
                      </td>
                      <td className="border border-gray-300 p-3 text-green-600">
                        {invoice.paid_amount.toFixed(2)} {currency}
                      </td>
                      <td className="border border-gray-300 p-3 text-red-600 font-bold">
                        {invoice.remaining_amount.toFixed(2)} {currency}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-200 font-bold">
                    <td colSpan="4" className="border border-gray-300 p-3 text-right">
                      الإجمالي:
                    </td>
                    <td className="border border-gray-300 p-3 text-red-600">
                      {totalRemaining.toFixed(2)} {currency}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 rounded-lg border-r-4 border-blue-500">
            <p className="text-sm text-gray-700">
              💡 <strong>ملاحظة:</strong> سيتم توزيع المبلغ المدفوع على الفواتير بترتيب التاريخ من الأقدم للأحدث
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Work Orders Component
const WorkOrders = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [workOrders, setWorkOrders] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [newWorkOrder, setNewWorkOrder] = useState({
    title: '',
    description: '',
    priority: 'عادي'
  });
  const [showAddToExisting, setShowAddToExisting] = useState(false);
  const [selectedWorkOrderId, setSelectedWorkOrderId] = useState('');
  const [selectedInvoiceForAdd, setSelectedInvoiceForAdd] = useState('');

  useEffect(() => {
    fetchWorkOrders();
    fetchInvoices();
  }, []);

  const fetchWorkOrders = async () => {
    try {
      const response = await axios.get(`${API}/work-orders`);
      setWorkOrders(response.data);
    } catch (error) {
      console.error('Error fetching work orders:', error);
      setWorkOrders([]); // Set empty array on error
    }
  };

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
    }
  };

  const toggleInvoiceSelection = (invoiceId) => {
    setSelectedInvoices(prev =>
      prev.includes(invoiceId)
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const createWorkOrderFromMultipleInvoices = async () => {
    if (selectedInvoices.length === 0) {
      alert('الرجاء اختيار فاتورة واحدة على الأقل');
      return;
    }

    if (!newWorkOrder.title.trim()) {
      alert('الرجاء إدخال عنوان أمر الشغل');
      return;
    }

    try {
      // Get selected invoices data
      const selectedInvoicesData = invoices.filter(inv => selectedInvoices.includes(inv.id));

      // Clean invoices data (remove MongoDB ObjectIds)
      const cleanInvoices = selectedInvoicesData.map(inv => {
        const cleanInv = { ...inv };
        if (cleanInv._id) delete cleanInv._id;
        return cleanInv;
      });

      // Create work order with multiple invoices
      const workOrderData = {
        title: newWorkOrder.title,
        description: newWorkOrder.description,
        priority: newWorkOrder.priority,
        invoices: cleanInvoices,
        total_amount: cleanInvoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0),
        total_items: cleanInvoices.reduce((sum, inv) => sum + (inv.items?.length || 0), 0)
      };

      const response = await axios.post(`${API}/work-orders/multiple`, workOrderData);

      if (response.data) {
        alert('تم إنشاء أمر الشغل بنجاح');

        // Reset form
        setSelectedInvoices([]);
        setNewWorkOrder({
          title: '',
          description: '',
          priority: 'عادي'
        });

        // Refresh work orders list
        await fetchWorkOrders();
      }
    } catch (error) {
      console.error('Error creating work order:', error);
      alert('حدث خطأ في إنشاء أمر الشغل: ' + (error.response?.data?.detail || error.message));
    }
  };

  const addInvoiceToExistingWorkOrder = async () => {
    if (!selectedWorkOrderId || !selectedInvoiceForAdd) {
      alert('الرجاء اختيار أمر الشغل والفاتورة');
      return;
    }

    try {
      const response = await axios.put(`${API}/work-orders/${selectedWorkOrderId}/add-invoice`, null, {
        params: { invoice_id: selectedInvoiceForAdd }
      });

      if (response.data) {
        alert('تم إضافة الفاتورة إلى أمر الشغل بنجاح');

        // Reset form
        setSelectedWorkOrderId('');
        setSelectedInvoiceForAdd('');
        setShowAddToExisting(false);

        // Refresh work orders list
        await fetchWorkOrders();
      }
    } catch (error) {
      console.error('Error adding invoice to work order:', error);
      alert('حدث خطأ في إضافة الفاتورة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getInvoiceDetails = (invoiceId) => {
    return invoices.find(inv => inv.id === invoiceId);
  };

  const getAvailableInvoices = () => {
    // Show invoices that are "تم التنفيذ" or "انتظار"
    return invoices.filter(invoice =>
      invoice.status === 'تم التنفيذ' || invoice.status === 'انتظار'
    );
  };

  const getAvailableInvoicesForAdd = () => {
    // Get invoices not already in the selected work order
    if (!selectedWorkOrderId) return getAvailableInvoices();

    const selectedWorkOrder = workOrders.find(wo => wo.id === selectedWorkOrderId);
    if (!selectedWorkOrder) return getAvailableInvoices();

    const usedInvoiceIds = selectedWorkOrder.invoices?.map(inv => inv.id) || [];

    return getAvailableInvoices().filter(invoice =>
      !usedInvoiceIds.includes(invoice.id)
    );
  };

  const printWorkOrder = (workOrder) => {
    const workOrderInvoices = workOrder.invoices?.map(invoiceData =>
      invoices.find(inv => inv.id === invoiceData.id) || invoiceData
    ).filter(inv => inv) || [];

    const totalAmount = workOrderInvoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0);
    const totalItems = workOrderInvoices.reduce((sum, inv) => sum + (inv.items?.length || 0), 0);

    const printContent = `
      <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
        <div style="text-align: center; margin-bottom: 20px;">
          <h1>ماستر سيل</h1>
          <p>الحرفيين شارع السوبر جيت - 01020630677</p>
          <h2 style="color: #333; margin-top: 20px;">أمر شغل</h2>
        </div>
        
        <div style="margin-bottom: 20px;">
          <strong>رقم أمر الشغل:</strong> ${workOrder.id}<br>
          <strong>العنوان:</strong> ${workOrder.title || `أمر شغل #${workOrder.id.slice(-8)}`}<br>
          <strong>التاريخ:</strong> ${new Date(workOrder.created_at).toLocaleDateString('ar-EG')}<br>
          <strong>الحالة:</strong> ${workOrder.status || 'جديد'}<br>
          <strong>عدد الفواتير:</strong> ${workOrderInvoices.length}<br>
          <strong>إجمالي المبلغ:</strong> ${currency} ${totalAmount.toFixed(2)}
          ${workOrder.description ? `<br><strong>الوصف:</strong> ${workOrder.description}` : ''}
          ${workOrder.supervisor_name ? `<br><strong>المشرف على التصنيع:</strong> ${workOrder.supervisor_name}` : ''}
          ${workOrder.is_daily ? `<br><strong>نوع الأمر:</strong> أمر شغل يومي تلقائي` : ''}
        </div>

        <h3 style="color: #333; margin-bottom: 10px;">الفواتير المدرجة:</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <thead>
            <tr style="background-color: #f0f0f0;">
              <th style="border: 1px solid #ddd; padding: 8px;">رقم الفاتورة</th>
              <th style="border: 1px solid #ddd; padding: 8px;">العميل</th>
              <th style="border: 1px solid #ddd; padding: 8px;">التاريخ</th>
              <th style="border: 1px solid #ddd; padding: 8px;">المبلغ</th>
              <th style="border: 1px solid #ddd; padding: 8px;">عدد المنتجات</th>
            </tr>
          </thead>
          <tbody>
            ${workOrderInvoices.map(invoice => `
              <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">${invoice.invoice_number}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${invoice.customer_name}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${new Date(invoice.date).toLocaleDateString('ar-EG')}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${currency} ${invoice.total_amount?.toFixed(2) || '0.00'}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${invoice.items?.length || 0}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <h3 style="color: #333; margin-bottom: 10px;">تفاصيل المنتجات:</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
          <thead>
            <tr style="background-color: #f0f0f0;">
              <th style="border: 1px solid #ddd; padding: 8px;">رقم الفاتورة</th>
              <th style="border: 1px solid #ddd; padding: 8px;">نوع السيل</th>
              <th style="border: 1px solid #ddd; padding: 8px;">نوع الخامة</th>
              <th style="border: 1px solid #ddd; padding: 8px;">المقاس</th>
              <th style="border: 1px solid #ddd; padding: 8px;">الكمية</th>
              <th style="border: 1px solid #ddd; padding: 8px;">الخامة المستخدمة</th>
              <th style="border: 1px solid #ddd; padding: 8px;">كود الوحدة</th>
            </tr>
          </thead>
          <tbody>
            ${workOrderInvoices.map(invoice =>
      invoice.items?.map(item => `
                <tr>
                  <td style="border: 1px solid #ddd; padding: 8px;">${invoice.invoice_number}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">${item.local_product_details ? item.local_product_details.product_type : (item.seal_type || 'غير محدد')}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">${item.local_product_details ? 'محلي' : (item.material_type || 'غير محدد')}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">${item.local_product_details ? `${item.local_product_details.product_size} - ${item.local_product_details.product_type}` : (item.inner_diameter && item.outer_diameter && item.height ? `${item.inner_diameter} × ${item.outer_diameter} × ${item.height}${item.wall_height ? ` (ارتفاع الحيطة: ${item.wall_height})` : ''}` : 'غير محدد')}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">${item.quantity}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">${item.local_product_details ? 'محلي' : (item.material_used || 'غير محدد')}</td>
                  <td style="border: 1px solid #ddd; padding: 8px;">
                    ${item.local_product_details ?
          'محلي' :
          item.material_details ?
            (item.material_details.is_finished_product ?
              'مخزن انتاج تام' :
              `${item.material_details.unit_code} / ${item.material_details.inner_diameter}-${item.material_details.outer_diameter}`
            ) :
            `${item.material_used || 'غير محدد'} / معلومات غير متوفرة`
        }
                  </td>
                </tr>
              `).join('') || ''
    ).join('')}
          </tbody>
        </table>
        
        <div style="margin-top: 40px; border-top: 1px solid #ddd; padding-top: 20px;">
          <div style="float: left;">
            <strong>ملاحظات التصنيع:</strong><br>
            <div style="margin-top: 10px; height: 50px; border: 1px solid #ddd;"></div>
          </div>
          <div style="float: right;">
            <strong>توقيع المسؤول:</strong><br>
            <div style="margin-top: 10px; height: 50px; border: 1px solid #ddd; width: 150px;"></div>
          </div>
          <div style="clear: both;"></div>
        </div>
      </div>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  };

  const clearAllWorkOrders = async () => {
    if (!confirm('هل أنت متأكد من حذف جميع أوامر الشغل؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    try {
      await axios.delete(`${API}/work-orders/clear-all`);
      fetchWorkOrders();
      alert('تم حذف جميع أوامر الشغل');
    } catch (error) {
      console.error('Error clearing work orders:', error);
      alert('حدث خطأ في حذف البيانات');
    }
  };

  const deleteWorkOrder = async (workOrderId) => {
    if (!confirm('هل أنت متأكد من حذف أمر الشغل هذا؟')) return;

    try {
      await axios.delete(`${API}/work-orders/${workOrderId}`);
      fetchWorkOrders();
      alert('تم حذف أمر الشغل بنجاح');
    } catch (error) {
      console.error('Error deleting work order:', error);
      alert('حدث خطأ في حذف أمر الشغل');
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">أمر شغل</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button
            onClick={clearAllWorkOrders}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            حذف الكل
          </button>
          <button
            onClick={() => { fetchWorkOrders(); fetchInvoices(); }}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            طباعة تقرير
          </button>
          <button
            onClick={() => setShowAddToExisting(!showAddToExisting)}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
            {showAddToExisting ? 'إخفاء' : 'إضافة فاتورة لأمر موجود'}
          </button>
          <select className="border border-gray-300 rounded px-3 py-2">
            <option>يومي</option>
            <option>أسبوعي</option>
            <option>شهري</option>
            <option>سنوي</option>
          </select>
        </div>
      </div>

      {/* Add Invoice to Existing Work Order */}
      {showAddToExisting && (
        <div className="bg-yellow-50 p-6 rounded-lg shadow-md mb-6 border border-yellow-200">
          <h3 className="text-lg font-semibold mb-4 text-yellow-800">إضافة فاتورة إلى أمر شغل موجود</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">اختيار أمر الشغل</label>
              <select
                value={selectedWorkOrderId}
                onChange={(e) => setSelectedWorkOrderId(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
              >
                <option value="">اختر أمر الشغل</option>
                {workOrders.map(workOrder => (
                  <option key={workOrder.id} value={workOrder.id}>
                    {workOrder.title || `أمر شغل #${workOrder.id.slice(-8)}`}
                    ({workOrder.invoices?.length || 0} فاتورة)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">اختيار الفاتورة</label>
              <select
                value={selectedInvoiceForAdd}
                onChange={(e) => setSelectedInvoiceForAdd(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                disabled={!selectedWorkOrderId}
              >
                <option value="">اختر الفاتورة</option>
                {getAvailableInvoicesForAdd().map(invoice => (
                  <option key={invoice.id} value={invoice.id}>
                    {invoice.invoice_number} - {invoice.customer_name}
                    ({currency} {invoice.total_amount?.toFixed(2) || '0.00'})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex space-x-4 space-x-reverse">
            <button
              onClick={addInvoiceToExistingWorkOrder}
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
              disabled={!selectedWorkOrderId || !selectedInvoiceForAdd}
            >
              إضافة الفاتورة
            </button>
            <button
              onClick={() => {
                setShowAddToExisting(false);
                setSelectedWorkOrderId('');
                setSelectedInvoiceForAdd('');
              }}
              className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600"
            >
              إلغاء
            </button>
          </div>
        </div>
      )}

      {/* Create Work Order from Multiple Invoices */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">إنشاء أمر شغل جديد</h3>

        {/* Work Order Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">عنوان أمر الشغل *</label>
            <input
              type="text"
              value={newWorkOrder.title}
              onChange={(e) => setNewWorkOrder({ ...newWorkOrder, title: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="مثال: أمر شغل رقم 1 - يناير 2025"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الأولوية</label>
            <select
              value={newWorkOrder.priority}
              onChange={(e) => setNewWorkOrder({ ...newWorkOrder, priority: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="عادي">عادي</option>
              <option value="مهم">مهم</option>
              <option value="طارئ">طارئ</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الفواتير المختارة</label>
            <div className="p-2 bg-gray-100 rounded">
              {selectedInvoices.length} فاتورة محددة
            </div>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">وصف أمر الشغل</label>
          <textarea
            value={newWorkOrder.description}
            onChange={(e) => setNewWorkOrder({ ...newWorkOrder, description: e.target.value })}
            className="w-full p-2 border border-gray-300 rounded h-20"
            placeholder="وصف إضافي (اختياري)"
          />
        </div>

        <h4 className="font-medium mb-2">اختيار الفواتير:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4 max-h-60 overflow-y-auto border rounded p-4">
          {getAvailableInvoices().map(invoice => (
            <div
              key={invoice.id}
              className={`border rounded-lg p-3 cursor-pointer transition-colors ${selectedInvoices.includes(invoice.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:bg-gray-50'
                }`}
              onClick={() => toggleInvoiceSelection(invoice.id)}
            >
              <div className="flex items-center mb-2">
                <input
                  type="checkbox"
                  checked={selectedInvoices.includes(invoice.id)}
                  onChange={() => { }}
                  className="ml-2"
                />
                <h5 className="font-semibold">{invoice.invoice_number}</h5>
              </div>
              <p className="text-sm text-gray-600">العميل: {invoice.customer_name}</p>
              <p className="text-sm text-gray-600">
                التاريخ: {new Date(invoice.date).toLocaleDateString('ar-EG')}
              </p>
              <p className="text-sm font-medium">
                المبلغ: {currency} {invoice.total_amount?.toFixed(2) || '0.00'}
              </p>
              <p className="text-sm">
                المنتجات: {invoice.items?.length || 0} صنف
              </p>
              <span className={`inline-block px-2 py-1 rounded text-xs mt-1 ${invoice.status === 'تم التنفيذ'
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
                }`}>
                {invoice.status}
              </span>
            </div>
          ))}
        </div>

        {getAvailableInvoices().length === 0 && (
          <div className="text-center py-8 text-gray-500">
            لا توجد فواتير متاحة لإنشاء أمر شغل
          </div>
        )}

        {selectedInvoices.length > 0 && (
          <div className="mb-4 p-3 bg-blue-100 rounded">
            <h5 className="font-semibold text-blue-800">ملخص أمر الشغل:</h5>
            <p className="text-blue-700">
              إجمالي الفواتير: {selectedInvoices.length} فاتورة
            </p>
            <p className="text-blue-700">
              إجمالي المبلغ: {currency} {invoices
                .filter(inv => selectedInvoices.includes(inv.id))
                .reduce((sum, inv) => sum + (inv.total_amount || 0), 0)
                .toFixed(2)}
            </p>
            <p className="text-blue-700">
              إجمالي المنتجات: {invoices
                .filter(inv => selectedInvoices.includes(inv.id))
                .reduce((sum, inv) => sum + (inv.items?.length || 0), 0)} صنف
            </p>
          </div>
        )}

        <button
          onClick={createWorkOrderFromMultipleInvoices}
          className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
          disabled={selectedInvoices.length === 0}
        >
          إنشاء أمر الشغل ({selectedInvoices.length} فاتورة)
        </button>
      </div>

      {/* Work Orders List */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">أوامر الشغل ({workOrders.length})</h3>

        {workOrders.map(workOrder => {
          // Handle both single invoice and multiple invoices work orders
          const workOrderInvoices = workOrder.invoices || (workOrder.invoice_id ? [getInvoiceDetails(workOrder.invoice_id)] : []);

          return (
            <div key={workOrder.id} className="border rounded-lg p-4 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="font-semibold text-lg">
                    {workOrder.title || `أمر شغل #${workOrder.id.slice(-8)}`}
                  </h4>
                  <p><strong>الأولوية:</strong>
                    <span className={`mr-2 px-2 py-1 rounded text-sm ${workOrder.priority === 'طارئ' ? 'bg-red-100 text-red-800' :
                      workOrder.priority === 'مهم' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                      {workOrder.priority || 'عادي'}
                    </span>
                  </p>
                  <p><strong>تاريخ الإنشاء:</strong> {new Date(workOrder.created_at).toLocaleDateString('ar-EG')}</p>
                  <p><strong>عدد الفواتير:</strong> {workOrderInvoices.filter(inv => inv).length}</p>
                </div>

                <div>
                  <p><strong>الحالة:</strong>
                    <span className="mr-2 px-2 py-1 rounded text-sm bg-blue-100 text-blue-800">
                      {workOrder.status || 'جديد'}
                    </span>
                  </p>
                  <p><strong>إجمالي المبلغ:</strong>
                    {currency} {workOrder.total_amount?.toFixed(2) ||
                      workOrderInvoices.reduce((sum, inv) => sum + (inv?.total_amount || 0), 0).toFixed(2)}
                  </p>
                  {workOrder.description && (
                    <p><strong>الوصف:</strong> {workOrder.description}</p>
                  )}
                  {workOrder.supervisor_name && (
                    <p><strong>المشرف على التصنيع:</strong> {workOrder.supervisor_name}</p>
                  )}
                  {workOrder.is_daily && (
                    <p><strong>نوع الأمر:</strong> <span className="text-green-600">أمر شغل يومي تلقائي</span></p>
                  )}
                </div>
              </div>

              {/* Work Order Invoices */}
              <div className="mb-4">
                <h5 className="font-medium mb-2">الفواتير المدرجة:</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {workOrderInvoices.filter(invoice => invoice).map((invoice, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded border">
                      <p><strong>رقم الفاتورة:</strong> {invoice.invoice_number}</p>
                      <p><strong>العميل:</strong> {invoice.customer_name}</p>
                      <p><strong>المبلغ:</strong> {currency} {invoice.total_amount?.toFixed(2) || '0.00'}</p>
                      <p><strong>المنتجات:</strong> {invoice.items?.length || 0} صنف</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Work Order Items Details */}
              <div className="overflow-x-auto mb-4">
                <h5 className="font-medium mb-2">تفاصيل المنتجات:</h5>
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 p-2">رقم الفاتورة</th>
                      <th className="border border-gray-300 p-2">نوع السيل</th>
                      <th className="border border-gray-300 p-2">نوع الخامة</th>
                      <th className="border border-gray-300 p-2">المقاس</th>
                      <th className="border border-gray-300 p-2">الكمية</th>
                      <th className="border border-gray-300 p-2">الخامة المستخدمة</th>
                      <th className="border border-gray-300 p-2">كود الوحدة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workOrderInvoices.filter(invoice => invoice).map(invoice =>
                      invoice.items?.map((item, itemIndex) => (
                        <tr key={`${invoice.id}-${itemIndex}`}>
                          <td className="border border-gray-300 p-2">{invoice.invoice_number}</td>
                          <td className="border border-gray-300 p-2">{item.seal_type}</td>
                          <td className="border border-gray-300 p-2">{item.material_type}</td>
                          <td className="border border-gray-300 p-2">
                            {item.inner_diameter} × {item.outer_diameter} × {item.height}
                          </td>
                          <td className="border border-gray-300 p-2">{item.quantity}</td>
                          <td className="border border-gray-300 p-2">
                            {item.material_details ? (
                              item.material_details.is_finished_product ? (
                                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                  منتج جاهز
                                </span>
                              ) : (
                                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                                  {item.material_details.material_type}
                                </span>
                              )
                            ) : (
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                                {item.material_used || 'غير محدد'}
                              </span>
                            )}
                          </td>
                          <td className="border border-gray-300 p-2">
                            <div className="font-mono text-sm">
                              {item.material_details ? (
                                item.material_details.is_finished_product ? (
                                  <div className="text-center font-semibold text-blue-600">
                                    مخزن انتاج تام
                                  </div>
                                ) : (
                                  <div>
                                    <div className="font-semibold">
                                      {item.unit_code_display || item.material_details.unit_code}
                                    </div>
                                    <div className="text-xs text-gray-600">
                                      {item.material_details.inner_diameter} - {item.material_details.outer_diameter}
                                    </div>
                                  </div>
                                )
                              ) : (
                                // للبيانات القديمة أو عندما لا توجد material_details
                                <div>
                                  <div className="font-semibold">{item.material_used || 'غير محدد'}</div>
                                  <div className="text-xs text-gray-600">
                                    معلومات الخامة غير متوفرة
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )) || []
                    )}
                  </tbody>
                </table>
              </div>

              {/* Work Order Actions */}
              <div className="flex space-x-4 space-x-reverse">
                <button
                  onClick={() => printWorkOrder(workOrder)}
                  className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                  طباعة أمر الشغل
                </button>
                <button className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600">
                  تعديل الحالة
                </button>
                <button
                  onClick={() => {
                    setSelectedWorkOrderId(workOrder.id);
                    setShowAddToExisting(true);
                  }}
                  className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
                  إضافة فاتورة
                </button>
                <button
                  onClick={() => deleteWorkOrder(workOrder.id)}
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                  حذف
                </button>
              </div>
            </div>
          );
        })}

        {workOrders.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            لا توجد أوامر شغل
          </div>
        )}
      </div>
    </div>
  );
};

// Treasury Management Component
const Treasury = () => {
  const { user, appSettings } = useAuth(); // للحصول على معلومات المستخدم الحالي
  const currency = appSettings?.currency || 'ج.م';
  const yadElsawyName = user?.username === 'Faster' ? 'خزنه مؤقته' : 'يد الصاوي';
  const [accounts, setAccounts] = useState([
    { id: 'cash', name: 'نقدي', balance: 0, transactions: [] },
    { id: 'vodafone_elsawy', name: 'فودافون 010', balance: 0, transactions: [] },
    { id: 'vodafone_wael', name: 'كاش 0100', balance: 0, transactions: [] },
    { id: 'deferred', name: 'آجل', balance: 0, transactions: [] },
    { id: 'instapay', name: 'انستاباي', balance: 0, transactions: [] },
    { id: 'yad_elsawy', name: yadElsawyName, balance: 0, transactions: [] }
  ]);

  const [selectedAccount, setSelectedAccount] = useState('cash');
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferData, setTransferData] = useState({
    from: 'cash',
    to: 'vodafone_elsawy',
    amount: '',
    notes: ''
  });

  const [manualTransaction, setManualTransaction] = useState({
    account: 'cash',
    type: 'income', // income or expense
    amount: '',
    description: '',
    notes: ''
  });

  const [showManualForm, setShowManualForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState(''); // إضافة البحث

  // Edit transaction states (Master only)
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [editForm, setEditForm] = useState({
    description: '',
    reference: '',
    amount: ''
  });

  useEffect(() => {
    fetchTreasuryData();
  }, []);

  const fetchTreasuryData = async () => {
    try {
      // Fetch balances and transactions from backend
      const balancesResponse = await axios.get(`${API}/treasury/balances`);
      const transactionsResponse = await axios.get(`${API}/treasury/transactions`);
      const invoicesResponse = await axios.get(`${API}/invoices`);
      const expensesResponse = await axios.get(`${API}/expenses`);

      const balances = balancesResponse.data;
      const manualTransactions = transactionsResponse.data;
      const invoices = invoicesResponse.data;
      const expenses = expensesResponse.data;

      // Update accounts with balances and transactions
      const updatedAccounts = accounts.map(account => {
        let transactions = [];

        // Add invoice transactions
        invoices.forEach(invoice => {
          const paymentMethodMap = {
            'نقدي': 'cash',
            'فودافون 010': 'vodafone_elsawy',
            'كاش 0100': 'vodafone_wael',
            'آجل': 'deferred',
            'انستاباي': 'instapay',
            'يد الصاوي': 'yad_elsawy'
          };

          if (paymentMethodMap[invoice.payment_method] === account.id) {
            transactions.push({
              id: `inv-${invoice.id}`,
              type: 'income',
              amount: invoice.display_amount || invoice.total_amount || 0,  // استخدام display_amount إذا موجود
              original_amount: invoice.total_amount || 0,  // المبلغ الأصلي للرصيد
              description: invoice.display_description || `فاتورة رقم ${invoice.invoice_number}`,  // استخدام display_description إذا موجود
              date: invoice.date,
              reference: invoice.display_reference || `العميل: ${invoice.customer_name}`,  // استخدام display_reference إذا موجود
              canEditAmount: true,  // يمكن تعديل المبلغ
              invoice_id: invoice.id,
              invoice_number: invoice.invoice_number,
              customer_name: invoice.customer_name
            });
          }
        });

        // Add expense transactions (only from cash account)
        if (account.id === 'cash') {
          expenses.forEach(expense => {
            transactions.push({
              id: `exp-${expense.id}`,
              type: 'expense',
              amount: expense.amount || 0,
              description: expense.description || 'مصروف',
              date: expense.date,
              category: expense.category
            });
          });
        }

        // Add manual transactions
        manualTransactions
          .filter(transaction => transaction.account_id === account.id)
          .forEach(transaction => {
            transactions.push({
              id: transaction.id,
              type: transaction.transaction_type,
              amount: transaction.amount,
              description: transaction.description,
              date: transaction.date,
              reference: transaction.reference
            });
          });

        return {
          ...account,
          balance: balances[account.id] || 0,
          transactions: transactions.sort((a, b) => new Date(b.date) - new Date(a.date))
        };
      });

      setAccounts(updatedAccounts);
    } catch (error) {
      console.error('Error fetching treasury data:', error);
    }
  };

  const handleTransfer = async () => {
    if (!transferData.amount || parseFloat(transferData.amount) <= 0) {
      alert('الرجاء إدخال مبلغ صحيح');
      return;
    }

    const amount = parseFloat(transferData.amount);
    const fromAccount = accounts.find(acc => acc.id === transferData.from);

    if (fromAccount.balance < amount) {
      alert('الرصيد غير كافي');
      return;
    }

    try {
      await axios.post(`${API}/treasury/transfer`, {
        from_account: transferData.from,
        to_account: transferData.to,
        amount: amount,
        notes: transferData.notes
      });

      // Refresh data
      fetchTreasuryData();

      setShowTransferModal(false);
      setTransferData({ from: 'cash', to: 'vodafone_elsawy', amount: '', notes: '' });
      alert('تم التحويل بنجاح');
    } catch (error) {
      console.error('Error processing transfer:', error);
      alert('حدث خطأ في التحويل');
    }
  };

  const handleManualTransaction = async () => {
    if (!manualTransaction.amount || parseFloat(manualTransaction.amount) <= 0) {
      alert('الرجاء إدخال مبلغ صحيح');
      return;
    }

    const amount = parseFloat(manualTransaction.amount);

    try {
      await axios.post(`${API}/treasury/transactions`, {
        account_id: manualTransaction.account,
        transaction_type: manualTransaction.type,
        amount: amount,
        description: manualTransaction.description,
        reference: manualTransaction.notes || 'إدخال يدوي'
      });

      // Refresh data
      fetchTreasuryData();

      setShowManualForm(false);
      setManualTransaction({
        account: 'cash',
        type: 'income',
        amount: '',
        description: '',
        notes: ''
      });
      alert('تم إضافة العملية بنجاح');
    } catch (error) {
      console.error('Error processing manual transaction:', error);
      alert('حدث خطأ في إضافة العملية');
    }
  };

  const clearAccount = async (accountId) => {
    if (!confirm('هل أنت متأكد من تصفير هذا الحساب؟ هذا الإجراء لا يمكن التراجع عنه.')) return;

    const account = accounts.find(acc => acc.id === accountId);
    if (!account || account.balance === 0) {
      alert('الحساب فارغ بالفعل أو غير موجود');
      return;
    }

    try {
      // If clearing "يد الصاوي", transfer to main treasury
      if (accountId === 'yad_elsawy') {
        // Transfer to main treasury
        await axios.post(`${API}/main-treasury/transfer-from-yad?amount=${account.balance}&username=${user.username}`);
      }

      // Create expense transaction to zero the account
      await axios.post(`${API}/treasury/transactions`, {
        account_id: accountId,
        transaction_type: 'expense',
        amount: account.balance,
        description: `تصفير حساب ${account.name}${accountId === 'yad_elsawy' ? ' (تم الترحيل للخزنة الرئيسية)' : ''}`,
        reference: 'تصفير بواسطة المدير'
      });

      // Refresh data
      fetchTreasuryData();

      if (accountId === 'yad_elsawy') {
        alert(`تم تصفير حساب ${account.name} بنجاح وترحيل المبلغ ${account.balance.toFixed(2)} ${currency} للخزنة الرئيسية`);
      } else {
        alert(`تم تصفير حساب ${account.name} بنجاح`);
      }
    } catch (error) {
      console.error('Error clearing account:', error);
      alert('حدث خطأ في تصفير الحساب');
    }
  };

  // Delete single transaction - Only for master
  const deleteTransaction = async (transactionId) => {
    if (user?.username !== 'master') {
      alert('غير مصرح لك بحذف السجلات');
      return;
    }

    // Ask user about deletion type
    const choice = confirm(
      '🗑️ حذف معاملة الخزينة\n\n' +
      'اختر نوع الحذف:\n\n' +
      '✅ اضغط "موافق" → إلغاء المعاملة وعكس تأثيرها (عكسي)\n' +
      '❌ اضغط "إلغاء" ثم "موافق" → حذف السجل فقط (بدون عكس)\n\n' +
      'الخيار الأول (عكسي) ينصح به لضمان دقة الأرصدة'
    );

    if (choice === null) return; // User pressed Escape

    const reverseTransaction = choice;

    // Final confirmation
    const confirmMsg = reverseTransaction
      ? 'تأكيد: سيتم إلغاء المعاملة وعكس تأثيرها على الحساب\n\nهل تريد المتابعة؟'
      : 'تأكيد: سيتم حذف السجل فقط بدون عكس المعاملة\n\n⚠️ قد يؤثر على دقة الأرصدة\n\nهل تريد المتابعة؟';

    if (!confirm(confirmMsg)) return;

    try {
      await axios.delete(`${API}/treasury/transactions/${transactionId}`, {
        params: {
          username: user.username,
          reverse_transaction: reverseTransaction
        }
      });

      alert('✅ تم حذف المعاملة بنجاح');
      fetchTreasuryData();
    } catch (error) {
      console.error('Error deleting transaction:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في حذف المعاملة');
    }
  };

  // Edit transaction record - Master only (without affecting balance)
  const openEditModal = (transaction) => {
    if (user?.username !== 'master') {
      alert('غير مصرح لك بتعديل السجلات');
      return;
    }

    // Check if this is an expense transaction (cannot edit)
    if (transaction.id?.startsWith('exp-')) {
      alert('لا يمكن تعديل سجلات المصروفات');
      return;
    }

    setEditingTransaction(transaction);
    setEditForm({
      description: transaction.description || '',
      reference: transaction.reference || '',
      amount: transaction.amount?.toString() || ''
    });
    setShowEditModal(true);
  };

  const saveEditTransaction = async () => {
    if (!editingTransaction) return;

    try {
      let response;

      // Check if this is an invoice display record (starts with inv-)
      if (editingTransaction.id?.startsWith('inv-')) {
        // Edit invoice display values
        const invoiceId = editingTransaction.invoice_id || editingTransaction.id.replace('inv-', '');
        response = await axios.put(
          `${API}/invoices/${invoiceId}/edit-display`,
          {
            display_amount: editForm.amount ? parseFloat(editForm.amount) : null,
            display_description: editForm.description || null,
            display_reference: editForm.reference || null
          },
          {
            params: { username: user.username }
          }
        );
      } else {
        // Edit treasury transaction (description and reference only)
        response = await axios.put(
          `${API}/treasury/transactions/${editingTransaction.id}/edit-record`,
          {
            description: editForm.description || null,
            reference: editForm.reference || null
          },
          {
            params: { username: user.username }
          }
        );
      }

      alert('✅ ' + response.data.message);
      setShowEditModal(false);
      setEditingTransaction(null);
      fetchTreasuryData();
    } catch (error) {
      console.error('Error editing transaction:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في تعديل السجل');
    }
  };

  // Treasury Reset Function - Only for Elsawy and Faster
  const resetTreasury = async () => {
    if (user?.username !== 'Elsawy' && user?.username !== 'Faster') {
      alert('غير مصرح لك بتنفيذ هذه العملية');
      return;
    }

    // Triple confirmation for this critical operation
    const firstConfirm = confirm('⚠️ تحذير: هذا الإجراء سيحذف جميع بيانات الخزينة ولا يمكن التراجع عنه!\nهل أنت متأكد من المتابعة؟');
    if (!firstConfirm) return;

    const secondConfirm = confirm('⚠️ تأكيد ثاني: سيتم حذف جميع المعاملات والأرصدة نهائياً!\nاكتب "نعم" للتأكيد:');
    if (!secondConfirm) return;

    const finalConfirm = prompt('⚠️ للتأكيد النهائي، اكتب بالضبط: "احذف كل شيء"');
    if (finalConfirm !== 'احذف كل شيء') {
      alert('تم إلغاء العملية');
      return;
    }

    try {
      const response = await axios.post(`${API}/treasury/reset`, null, {
        params: { username: user.username }
      });

      alert(`✅ تم مسح جميع بيانات الخزينة بنجاح!\nتم حذف ${response.data.deleted_treasury_transactions} معاملة`);

      // Refresh data
      fetchTreasuryData();
    } catch (error) {
      console.error('Error resetting treasury:', error);
      alert('حدث خطأ في مسح الخزينة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const selectedAccountData = accounts.find(acc => acc.id === selectedAccount);

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">الخزينة - إدارة الأموال</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button
            onClick={() => setShowTransferModal(true)}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            تحويل أموال
          </button>
          <button
            onClick={() => setShowManualForm(true)}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إضافة عملية يدوية
          </button>
          <button
            onClick={fetchTreasuryData}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
            طباعة تقرير
          </button>
          {(user?.username === 'Elsawy' || user?.username === 'Faster') && (
            <button
              onClick={resetTreasury}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 font-bold border-2 border-red-800">
              ⚠️ مسح الخزينة بالكامل
            </button>
          )}
          {(user?.username === 'Elsawy' || user?.username === 'Faster') && selectedAccount === 'yad_elsawy' && selectedAccountData?.balance > 0 && (
            <button
              onClick={() => clearAccount(selectedAccount)}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
              تصفير حساب {yadElsawyName}
            </button>
          )}
        </div>
      </div>

      {/* Accounts Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        {accounts.map(account => (
          <div
            key={account.id}
            className={`p-4 rounded-lg shadow cursor-pointer transition-colors ${selectedAccount === account.id
              ? 'bg-blue-100 border-2 border-blue-500'
              : 'bg-white hover:bg-gray-50'
              }`}
            onClick={() => setSelectedAccount(account.id)}
          >
            <h3 className="font-semibold text-gray-800 mb-2">{account.name}</h3>
            <p className={`text-2xl font-bold ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
              {currency} {account.balance.toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {account.transactions.length} عملية
            </p>
          </div>
        ))}
      </div>

      {/* Account Details */}
      {selectedAccountData && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">
            تفاصيل حساب: {selectedAccountData.name}
          </h3>

          {/* Search Bar */}
          <div className="mb-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="البحث في المعاملات..."
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">التاريخ</th>
                  <th className="border border-gray-300 p-2">النوع</th>
                  <th className="border border-gray-300 p-2">الوصف</th>
                  <th className="border border-gray-300 p-2">المبلغ</th>
                  <th className="border border-gray-300 p-2">المرجع</th>
                  {user?.username === 'master' && (
                    <th className="border border-gray-300 p-2">إجراءات</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {selectedAccountData.transactions
                  .filter(transaction =>
                    transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (transaction.reference && transaction.reference.toLowerCase().includes(searchTerm.toLowerCase())) ||
                    (transaction.category && transaction.category.toLowerCase().includes(searchTerm.toLowerCase()))
                  )
                  .map((transaction, index) => (
                    <tr key={transaction.id || index}>
                      <td className="border border-gray-300 p-2">
                        {new Date(transaction.date).toLocaleDateString('ar-EG')}
                      </td>
                      <td className="border border-gray-300 p-2">
                        <span className={`px-2 py-1 rounded text-xs ${transaction.type === 'income' ? 'bg-green-100 text-green-800' :
                          transaction.type === 'expense' ? 'bg-red-100 text-red-800' :
                            transaction.type === 'transfer_in' ? 'bg-blue-100 text-blue-800' :
                              'bg-orange-100 text-orange-800'
                          }`}>
                          {transaction.type === 'income' ? 'دخل' :
                            transaction.type === 'expense' ? 'مصروف' :
                              transaction.type === 'transfer_in' ? 'تحويل وارد' : 'تحويل صادر'}
                        </span>
                      </td>
                      <td className="border border-gray-300 p-2">{transaction.description}</td>
                      <td className="border border-gray-300 p-2">
                        <span className={
                          transaction.type === 'income' || transaction.type === 'transfer_in'
                            ? 'text-green-600 font-semibold'
                            : 'text-red-600 font-semibold'
                        }>
                          {transaction.type === 'income' || transaction.type === 'transfer_in' ? '+' : '-'}
                          {currency} {transaction.amount.toFixed(2)}
                        </span>
                      </td>
                      <td className="border border-gray-300 p-2 text-sm text-gray-600">
                        {transaction.reference || transaction.category || '-'}
                      </td>
                      {user?.username === 'master' && (
                        <td className="border border-gray-300 p-2 text-center">
                          <div className="flex gap-2 justify-center">
                            <button
                              onClick={() => openEditModal(transaction)}
                              className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                              title="تعديل السجل (بدون تأثير على الرصيد)"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => deleteTransaction(transaction.id)}
                              className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600"
                              title="حذف المعاملة"
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
              </tbody>
            </table>

            {selectedAccountData.transactions.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                لا توجد عمليات لهذا الحساب
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">تحويل أموال بين الحسابات</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">من حساب</label>
                <select
                  value={transferData.from}
                  onChange={(e) => setTransferData({ ...transferData, from: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  {accounts.map(account => (
                    <option key={account.id} value={account.id}>
                      {account.name} ({currency} {account.balance.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">إلى حساب</label>
                <select
                  value={transferData.to}
                  onChange={(e) => setTransferData({ ...transferData, to: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  {accounts.filter(acc => acc.id !== transferData.from).map(account => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">المبلغ</label>
                <input
                  type="number"
                  value={transferData.amount}
                  onChange={(e) => setTransferData({ ...transferData, amount: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ملاحظات</label>
                <input
                  type="text"
                  value={transferData.notes}
                  onChange={(e) => setTransferData({ ...transferData, notes: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="ملاحظات إضافية (اختياري)"
                />
              </div>
            </div>

            <div className="flex space-x-4 space-x-reverse mt-6">
              <button
                onClick={handleTransfer}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                تأكيد التحويل
              </button>
              <button
                onClick={() => setShowTransferModal(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Transaction Modal */}
      {showManualForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">إضافة عملية يدوية</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">الحساب</label>
                <select
                  value={manualTransaction.account}
                  onChange={(e) => setManualTransaction({ ...manualTransaction, account: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  {accounts.map(account => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">نوع العملية</label>
                <select
                  value={manualTransaction.type}
                  onChange={(e) => setManualTransaction({ ...manualTransaction, type: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="income">دخل</option>
                  <option value="expense">مصروف</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">المبلغ</label>
                <input
                  type="number"
                  value={manualTransaction.amount}
                  onChange={(e) => setManualTransaction({ ...manualTransaction, amount: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">الوصف</label>
                <input
                  type="text"
                  value={manualTransaction.description}
                  onChange={(e) => setManualTransaction({ ...manualTransaction, description: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="وصف العملية"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ملاحظات</label>
                <input
                  type="text"
                  value={manualTransaction.notes}
                  onChange={(e) => setManualTransaction({ ...manualTransaction, notes: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="ملاحظات إضافية (اختياري)"
                />
              </div>
            </div>

            <div className="flex space-x-4 space-x-reverse mt-6">
              <button
                onClick={handleManualTransaction}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                إضافة العملية
              </button>
              <button
                onClick={() => setShowManualForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal - Master Only */}
      {showEditModal && editingTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-blue-800">
              ✏️ تعديل سجل المعاملة
            </h3>

            {editingTransaction.canEditAmount ? (
              <>
                <div className="bg-green-50 border border-green-300 rounded-lg p-3 mb-4">
                  <p className="text-green-800 text-sm">
                    ✅ يمكن تعديل المبلغ والوصف والمرجع في هذا السجل بدون التأثير على الرصيد الفعلي
                  </p>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-4">
                  <p className="text-gray-700 text-sm">
                    💰 المبلغ الأصلي (للرصيد): <span className="font-bold text-blue-600">{editingTransaction.original_amount?.toFixed(2)} {currency}</span>
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">الوصف</label>
                    <input
                      type="text"
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded"
                      placeholder="أدخل الوصف الجديد"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">المبلغ المعروض في السجل</label>
                    <input
                      type="number"
                      value={editForm.amount}
                      onChange={(e) => setEditForm({ ...editForm, amount: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded"
                      placeholder="أدخل المبلغ الجديد"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">المرجع</label>
                    <input
                      type="text"
                      value={editForm.reference}
                      onChange={(e) => setEditForm({ ...editForm, reference: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded"
                      placeholder="أدخل المرجع الجديد"
                    />
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-3 mb-4">
                  <p className="text-yellow-800 text-sm">
                    ⚠️ يمكن تعديل الوصف والمرجع فقط. المبلغ لا يمكن تعديله لأنه يؤثر على الرصيد.
                  </p>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-4">
                  <p className="text-gray-700 text-sm">
                    💰 المبلغ: <span className="font-bold">{editingTransaction.amount?.toFixed(2)} {currency}</span>
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">الوصف</label>
                    <input
                      type="text"
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded"
                      placeholder="أدخل الوصف الجديد"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">المرجع</label>
                    <input
                      type="text"
                      value={editForm.reference}
                      onChange={(e) => setEditForm({ ...editForm, reference: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded"
                      placeholder="أدخل المرجع الجديد"
                    />
                  </div>
                </div>
              </>
            )}

            <div className="flex gap-2 mt-6">
              <button
                onClick={saveEditTransaction}
                className="flex-1 bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
              >
                💾 حفظ التعديلات
              </button>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingTransaction(null);
                }}
                className="flex-1 bg-gray-400 text-white p-2 rounded hover:bg-gray-500"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Backup and Restore Component
const Backup = () => {
  const [backups, setBackups] = useState([]);
  const [driveFiles, setDriveFiles] = useState([]);
  const [driveStatus, setDriveStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [activeTab, setActiveTab] = useState('local'); // 'local' or 'drive'
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';

  // Bulk deletion states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteType, setDeleteType] = useState(''); // 'date', 'last-1', 'last-2'
  const [deleteDate, setDeleteDate] = useState('');

  useEffect(() => {
    fetchBackups();
    fetchDriveStatus();
  }, []);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/backup/list`);
      setBackups(response.data || []);
    } catch (error) {
      console.error('Error fetching backups:', error);
      alert('حدث خطأ في جلب النسخ الاحتياطية');
    } finally {
      setLoading(false);
    }
  };

  const fetchDriveStatus = async () => {
    try {
      const response = await axios.get(`${API}/backup/drive/status`);
      setDriveStatus(response.data);
    } catch (error) {
      console.error('Error fetching drive status:', error);
    }
  };

  const fetchDriveFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/backup/drive/list`);
      setDriveFiles(response.data.files || []);
    } catch (error) {
      console.error('Error fetching drive files:', error);
      alert('حدث خطأ في جلب ملفات Google Drive');
    } finally {
      setLoading(false);
    }
  };

  // Bulk deletion functions
  const openDeleteModal = (type) => {
    if (user?.username !== 'Elsawy') {
      alert('غير مصرح لك بتنفيذ هذه العملية');
      return;
    }
    setDeleteType(type);
    setDeletePassword('');
    setDeleteDate('');
    setShowDeleteModal(true);
  };

  const handleBulkDelete = async () => {
    if (!deletePassword) {
      alert('الرجاء إدخال كلمة المرور');
      return;
    }

    if (deleteType === 'date' && !deleteDate) {
      alert('الرجاء اختيار التاريخ');
      return;
    }

    const confirmMessage = deleteType === 'date'
      ? `هل أنت متأكد من حذف جميع فواتير يوم ${deleteDate}؟\n\n⚠️ سيتم:\n• نقل الفواتير للمحذوفة\n• استرجاع المواد للمخزن\n• عكس عمليات الخزينة`
      : deleteType === 'last-1'
        ? `هل أنت متأكد من حذف آخر فاتورة؟\n\n⚠️ سيتم:\n• نقل الفاتورة للمحذوفة\n• استرجاع المواد للمخزن\n• عكس عمليات الخزينة`
        : `هل أنت متأكد من حذف آخر فاتورتين؟\n\n⚠️ سيتم:\n• نقل الفواتير للمحذوفة\n• استرجاع المواد للمخزن\n• عكس عمليات الخزينة`;

    if (!confirm(confirmMessage)) {
      return;
    }

    setLoading(true);
    try {
      let response;

      if (deleteType === 'date') {
        response = await axios.post(`${API}/invoices/bulk-delete-by-date`, null, {
          params: {
            date: deleteDate,
            password: deletePassword,
            username: user.username
          }
        });
      } else {
        const count = deleteType === 'last-1' ? 1 : 2;
        response = await axios.post(`${API}/invoices/bulk-delete-last`, null, {
          params: {
            count: count,
            password: deletePassword,
            username: user.username
          }
        });
      }

      // Show detailed results
      const data = response.data;
      let message = `✅ ${data.message}\n\nعدد الفواتير المحذوفة: ${data.deleted_count}\n\n`;

      if (data.invoices && data.invoices.length > 0) {
        message += 'الفواتير المحذوفة:\n';
        data.invoices.forEach(inv => {
          message += `• ${inv.invoice_number} - ${inv.customer_name} - ${inv.total_amount} ${currency}\n`;
        });
      }

      alert(message);
      setShowDeleteModal(false);
      setDeletePassword('');
      setDeleteDate('');

    } catch (error) {
      console.error('Error deleting invoices:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في حذف الفواتير');
    } finally {
      setLoading(false);
    }
  };

  const checkBackupStatus = async (backupId, attempts = 0) => {
    try {
      const response = await axios.get(`${API}/backup/status/${backupId}`);
      const status = response.data.status;

      if (status === 'completed' || status === 'completed_with_drive') {
        setCreating(false);
        let message = `✅ تم إنشاء النسخة الاحتياطية بنجاح!\n\nإجمالي المستندات: ${response.data.total_documents}`;
        if (status === 'completed_with_drive') {
          message += '\n\n🌐 تم الرفع إلى Google Drive بنجاح!';
        }
        alert(message);
        fetchBackups();
        fetchDriveFiles();
      } else if (status === 'failed') {
        setCreating(false);
        alert('❌ فشلت عملية النسخ الاحتياطي\n\n' + (response.data.error || 'خطأ غير معروف'));
        fetchBackups();
      } else if (status === 'in_progress' && attempts < 60) {
        // Keep checking every 2 seconds for up to 2 minutes
        setTimeout(() => checkBackupStatus(backupId, attempts + 1), 2000);
      } else {
        // Timeout after 2 minutes
        setCreating(false);
        alert('⏱️ انتهت مهلة الانتظار. يرجى التحقق من قائمة النسخ الاحتياطية.');
        fetchBackups();
      }
    } catch (error) {
      console.error('Error checking backup status:', error);
      if (attempts < 60) {
        setTimeout(() => checkBackupStatus(backupId, attempts + 1), 2000);
      } else {
        setCreating(false);
        fetchBackups();
      }
    }
  };

  const createBackup = async () => {
    if (!confirm('هل تريد إنشاء نسخة احتياطية محلية الآن؟')) {
      return;
    }

    setCreating(true);
    try {
      const response = await axios.post(`${API}/backup/create`, null, {
        params: {
          username: user?.username
        }
      });

      // Start polling for status
      if (response.data.backup_id) {
        alert(`⏳ ${response.data.message}\n\nسيتم تحديث القائمة تلقائياً عند الانتهاء.`);
        checkBackupStatus(response.data.backup_id);
      } else {
        setCreating(false);
        alert('❌ فشل في بدء عملية النسخ الاحتياطي');
      }
    } catch (error) {
      console.error('Error creating backup:', error);
      alert('حدث خطأ في إنشاء النسخة الاحتياطية: ' + (error.response?.data?.detail || error.message));
      setCreating(false);
    }
  };

  const downloadBackup = async (backupId, createdAt) => {
    try {
      const response = await axios.get(`${API}/backup/download/${backupId}`, {
        responseType: 'blob'
      });

      // Create download link
      const timestamp = new Date(createdAt).toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `backup_${timestamp}.json`;
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      alert('✅ تم تنزيل النسخة الاحتياطية بنجاح!');
    } catch (error) {
      console.error('Error downloading backup:', error);
      alert('حدث خطأ في التنزيل: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    if (!file.name.endsWith('.json')) {
      alert('❌ يجب اختيار ملف JSON');
      event.target.value = '';
      return;
    }

    // Ask user what to do
    const action = confirm(
      `تم اختيار: ${file.name}\n\n` +
      `اختر الإجراء:\n\n` +
      `✅ موافق = إضافة النسخة للقائمة فقط (يمكنك استرجاعها لاحقاً)\n` +
      `❌ إلغاء = استرجاع البيانات مباشرة (سيحذف البيانات الحالية)\n\n` +
      `ماذا تريد؟`
    );

    if (action) {
      // Add to list only
      await uploadBackupFile(file, false);
    } else {
      // Ask for confirmation before restore
      if (confirm(`⚠️ تحذير!\n\nهل أنت متأكد من استرجاع البيانات مباشرة؟\n\nسيتم حذف جميع البيانات الحالية!\n\nهذا الإجراء لا يمكن التراجع عنه!`)) {
        await uploadBackupFile(file, true);
      }
    }

    // Reset input
    event.target.value = '';
  };

  const uploadBackupFile = async (file, restoreDirectly) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      let response;
      if (restoreDirectly) {
        // Restore directly
        response = await axios.post(`${API}/backup/restore-from-file`, formData, {
          params: { username: user?.username },
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        alert(`✅ ${response.data.message}\n\n` +
          `المجموعات المسترجعة: ${response.data.collections_restored}\n` +
          `إجمالي المستندات: ${response.data.total_documents}\n\n` +
          `سيتم إعادة تحميل الصفحة...`);

        setTimeout(() => window.location.reload(), 2000);
      } else {
        // Upload to list
        response = await axios.post(`${API}/backup/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        alert(`✅ ${response.data.message}\n\n` +
          `يمكنك الآن استرجاع هذه النسخة من القائمة`);

        fetchBackups();
      }
    } catch (error) {
      console.error('Error uploading backup:', error);
      alert('حدث خطأ: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const restoreBackup = async (backupId, createdAt) => {
    if (!confirm(`⚠️ تحذير خطير!\n\nهل أنت متأكد من استرجاع النسخة الاحتياطية؟\n\nالتاريخ: ${new Date(createdAt).toLocaleString('ar-EG')}\n\nسيتم حذف جميع البيانات الحالية واستبدالها بالنسخة الاحتياطية!\n\nهذا الإجراء لا يمكن التراجع عنه!`)) {
      return;
    }

    // Second confirmation
    if (!confirm('تأكيد نهائي: هل أنت متأكد تماماً؟')) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/backup/restore/${backupId}`, null, {
        params: { username: user?.username }
      });
      alert(`✅ ${response.data.message}\n\nالمجموعات المسترجعة: ${response.data.collections_restored}\nإجمالي المستندات: ${response.data.total_documents}\n\nيُنصح بإعادة تحميل الصفحة.`);

      // Reload page after successful restore
      if (confirm('هل تريد إعادة تحميل الصفحة الآن؟')) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error restoring backup:', error);
      alert('حدث خطأ في استرجاع النسخة الاحتياطية: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const deleteBackup = async (backupId, createdAt) => {
    if (!confirm(`هل تريد حذف النسخة الاحتياطية؟\n\nالتاريخ: ${new Date(createdAt).toLocaleString('ar-EG')}\n\nهذا الإجراء لا يمكن التراجع عنه!`)) {
      return;
    }

    try {
      await axios.delete(`${API}/backup/${backupId}`);
      alert('تم حذف النسخة الاحتياطية بنجاح');
      fetchBackups();
      fetchDriveFiles(); // Refresh Drive files too
    } catch (error) {
      console.error('Error deleting backup:', error);
      alert('حدث خطأ في حذف النسخة الاحتياطية: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Google Drive Functions
  const uploadToDrive = async (backupId) => {
    if (!driveStatus?.enabled) {
      alert('❌ Google Drive غير متصل!\n\nيرجى التحقق من إعدادات Google Drive.');
      return;
    }

    try {
      const response = await axios.post(`${API}/backup/${backupId}/upload-to-drive`);
      alert(`✅ ${response.data.message}`);
      fetchBackups();
      fetchDriveFiles();
    } catch (error) {
      console.error('Error uploading to Drive:', error);
      let errorMsg = 'حدث خطأ في رفع النسخة الاحتياطية:\n\n';

      if (error.response?.data?.detail) {
        errorMsg += error.response.data.detail;

        // Check for storage quota error
        if (error.response.data.detail.includes('storage quota') || error.response.data.detail.includes('403')) {
          errorMsg += '\n\n💡 الحل:\n';
          errorMsg += '1. افتح Google Drive\n';
          errorMsg += '2. ابحث عن مجلد "ماستر سيل"\n';
          errorMsg += '3. شارك المجلد مع:\n   master-seal-backup@master-seal-backup.iam.gserviceaccount.com\n';
          errorMsg += '4. اختر صلاحية "Editor"';
        }
      } else {
        errorMsg += error.message;
      }

      alert(errorMsg);
    }
  };

  const downloadFromDrive = async (fileId, fileName) => {
    try {
      const response = await axios.get(`${API}/backup/drive/download/${fileId}`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert('✅ تم تنزيل النسخة الاحتياطية بنجاح');
    } catch (error) {
      console.error('Error downloading from Drive:', error);
      alert('حدث خطأ في تنزيل الملف: ' + (error.response?.data?.detail || error.message));
    }
  };

  const restoreFromDrive = async (fileId, fileName) => {
    if (!confirm(`⚠️ تحذير!\n\nهل أنت متأكد من استرجاع النسخة الاحتياطية من Google Drive؟\n\nملف: ${fileName}\n\nسيتم حذف جميع البيانات الحالية!`)) {
      return;
    }

    if (!confirm('تأكيد نهائي: هل أنت متأكد تماماً؟')) {
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/backup/drive/restore/${fileId}`);
      alert(`✅ ${response.data.message}\n\nالمجموعات المسترجعة: ${response.data.collections_restored}\nإجمالي المستندات: ${response.data.total_documents}`);

      if (confirm('هل تريد إعادة تحميل الصفحة الآن؟')) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error restoring from Drive:', error);
      alert('حدث خطأ في الاسترجاع: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const deleteFromDrive = async (fileId, fileName) => {
    if (!confirm(`هل تريد حذف الملف من Google Drive؟\n\n${fileName}\n\nهذا الإجراء لا يمكن التراجع عنه!`)) {
      return;
    }

    try {
      await axios.delete(`${API}/backup/drive/${fileId}`);
      alert('تم حذف الملف من Google Drive بنجاح');
      fetchDriveFiles();
    } catch (error) {
      console.error('Error deleting from Drive:', error);
      alert('حدث خطأ في الحذف: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Switch tab and load data
  const switchTab = (tab) => {
    setActiveTab(tab);
    if (tab === 'drive' && driveFiles.length === 0) {
      fetchDriveFiles();
    }
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">إدارة النسخ الاحتياطي</h1>
        <div className="flex space-x-2 space-x-reverse flex-wrap gap-2">
          <button
            onClick={createBackup}
            disabled={creating}
            className={`px-6 py-2 rounded text-white ${creating ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600'
              }`}
          >
            {creating ? '⏳ جاري الإنشاء...' : '💾 إنشاء نسخة'}
          </button>
          <label className="bg-purple-500 text-white px-6 py-2 rounded hover:bg-purple-600 cursor-pointer">
            📤 استيراد نسخة
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
          <button
            onClick={fetchBackups}
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            🔄 تحديث
          </button>
        </div>
      </div>

      {/* Auto Backup Info */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg mb-6 border-r-4 border-blue-500">
        <h3 className="font-bold mb-2">📅 النسخ الاحتياطي التلقائي</h3>
        <p className="text-sm text-gray-700">
          يتم إنشاء نسخة احتياطية محلية تلقائياً كل يوم في تمام الساعة 7:00 مساءً.
          يمكنك تنزيل أي نسخة ورفعها يدوياً إلى Google Drive أو أي خدمة سحابية أخرى.
        </p>
      </div>

      {/* Bulk Invoice Deletion Section - Elsawy Only */}
      {user?.username === 'Elsawy' && (
        <div className="bg-gradient-to-r from-red-50 to-orange-100 p-6 rounded-lg mb-6 border-r-4 border-red-500">
          <h3 className="font-bold text-xl mb-4 flex items-center gap-2">
            🗑️ إدارة الفواتير - حذف جماعي
          </h3>
          <p className="text-sm text-gray-700 mb-4">
            ⚠️ <strong>تحذير:</strong> عند الحذف سيتم استرجاع المواد للمخزن وعكس عمليات الخزينة ونقل الفواتير للمحذوفة
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Delete by Date */}
            <button
              onClick={() => openDeleteModal('date')}
              className="bg-red-500 hover:bg-red-600 text-white px-6 py-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            >
              📅 حذف فواتير يوم معين
            </button>

            {/* Delete Last Invoice */}
            <button
              onClick={() => openDeleteModal('last-1')}
              className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            >
              🔴 حذف آخر فاتورة
            </button>

            {/* Delete Last 2 Invoices */}
            <button
              onClick={() => openDeleteModal('last-2')}
              className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            >
              🔴🔴 حذف آخر فاتورتين
            </button>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" dir="rtl">
          <div className="bg-white rounded-lg p-8 max-w-md w-full shadow-2xl">
            <h3 className="text-2xl font-bold mb-4 text-red-600">
              ⚠️ تأكيد الحذف
            </h3>

            <div className="mb-4 p-4 bg-yellow-50 border-r-4 border-yellow-500 rounded">
              <p className="text-sm text-gray-700">
                {deleteType === 'date'
                  ? '🗓️ سيتم حذف جميع فواتير اليوم المحدد'
                  : deleteType === 'last-1'
                    ? '📋 سيتم حذف آخر فاتورة'
                    : '📋📋 سيتم حذف آخر فاتورتين'
                }
              </p>
              <p className="text-xs text-gray-600 mt-2">
                ✓ استرجاع المواد<br />
                ✓ عكس الخزينة<br />
                ✓ نقل للمحذوفة
              </p>
            </div>

            {deleteType === 'date' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  اختر التاريخ:
                </label>
                <input
                  type="date"
                  value={deleteDate}
                  onChange={(e) => setDeleteDate(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:border-red-500 focus:outline-none"
                />
              </div>
            )}

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                كلمة المرور (200200):
              </label>
              <input
                type="password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleBulkDelete()}
                placeholder="أدخل كلمة المرور"
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-red-500 focus:outline-none"
                autoFocus
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleBulkDelete}
                disabled={loading}
                className={`flex-1 py-3 rounded-lg font-semibold text-white transition-colors ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'
                  }`}
              >
                {loading ? '⏳ جاري الحذف...' : '✅ تأكيد الحذف'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletePassword('');
                  setDeleteDate('');
                }}
                disabled={loading}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-3 rounded-lg font-semibold transition-colors"
              >
                ❌ إلغاء
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backups Table */}
      <div className="bg-white rounded-lg shadow-md overflow-x-auto">
        {loading && !creating ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">⏳ جاري التحميل...</p>
          </div>
        ) : backups.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">لا توجد نسخ احتياطية حتى الآن</p>
            <p className="text-sm text-gray-400 mt-2">اضغط على "إنشاء نسخة احتياطية" لإنشاء أول نسخة</p>
          </div>
        ) : (
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">التاريخ والوقت</th>
                <th className="border border-gray-300 p-2">أنشئت بواسطة</th>
                <th className="border border-gray-300 p-2">عدد المستندات</th>
                <th className="border border-gray-300 p-2">الحالة</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((backup) => (
                <tr key={backup.backup_id} className="hover:bg-gray-50">
                  <td className="border border-gray-300 p-2">
                    {new Date(backup.created_at).toLocaleString('ar-EG', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                    {backup.is_scheduled && (
                      <span className="block text-xs text-blue-600 mt-1">🤖 تلقائي</span>
                    )}
                  </td>
                  <td className="border border-gray-300 p-2">{backup.created_by}</td>
                  <td className="border border-gray-300 p-2 text-center font-medium">
                    {backup.total_documents || 0}
                  </td>
                  <td className="border border-gray-300 p-2 text-center">
                    {backup.status === 'in_progress' && (
                      <span className="text-orange-600 animate-pulse">⏳ جاري...</span>
                    )}
                    {backup.status === 'failed' && (
                      <span className="text-red-600">❌ فشل</span>
                    )}
                    {(backup.status === 'completed' || backup.status === 'completed_with_drive' || backup.status === 'completed_no_drive') && (
                      <span className="text-green-600">✅ مكتمل</span>
                    )}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse justify-center flex-wrap gap-1">
                      <button
                        onClick={() => downloadBackup(backup.backup_id, backup.created_at)}
                        className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                        title="تنزيل النسخة الاحتياطية"
                      >
                        ⬇️ تنزيل
                      </button>
                      <button
                        onClick={() => restoreBackup(backup.backup_id, backup.created_at)}
                        disabled={loading || backup.status === 'in_progress'}
                        className="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600 disabled:bg-gray-400"
                        title="استرجاع البيانات من هذه النسخة"
                      >
                        ↩️ استرجاع
                      </button>
                      <button
                        onClick={() => deleteBackup(backup.backup_id, backup.created_at)}
                        disabled={loading}
                        className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 disabled:bg-gray-400"
                        title="حذف النسخة الاحتياطية"
                      >
                        🗑️ حذف
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Google Drive Tab */}
      {activeTab === 'drive' && (
        <div className="bg-white rounded-lg shadow-md overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">⏳ جاري التحميل...</p>
            </div>
          ) : !driveStatus?.enabled ? (
            <div className="p-8 text-center">
              <p className="text-red-500">❌ Google Drive غير متصل</p>
              <p className="text-sm text-gray-400 mt-2">يرجى التحقق من إعدادات Google Drive</p>
            </div>
          ) : driveFiles.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">لا توجد ملفات في Google Drive</p>
              <p className="text-sm text-gray-400 mt-2">قم برفع نسخة احتياطية من التبويب السابق</p>
            </div>
          ) : (
            <table className="min-w-full border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">اسم الملف</th>
                  <th className="border border-gray-300 p-2">التاريخ</th>
                  <th className="border border-gray-300 p-2">الحجم</th>
                  <th className="border border-gray-300 p-2">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {driveFiles.map((file) => (
                  <tr key={file.id} className="hover:bg-gray-50">
                    <td className="border border-gray-300 p-2">
                      <a
                        href={file.webViewLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {file.name}
                      </a>
                    </td>
                    <td className="border border-gray-300 p-2">
                      {new Date(file.createdTime).toLocaleString('ar-EG', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="border border-gray-300 p-2 text-center">
                      {file.size ? `${(file.size / 1024).toFixed(2)} KB` : '-'}
                    </td>
                    <td className="border border-gray-300 p-2">
                      <div className="flex space-x-2 space-x-reverse justify-center flex-wrap gap-1">
                        <button
                          onClick={() => downloadFromDrive(file.id, file.name)}
                          className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                        >
                          ⬇️ تنزيل
                        </button>
                        <button
                          onClick={() => restoreFromDrive(file.id, file.name)}
                          disabled={loading}
                          className="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600 disabled:bg-gray-400"
                        >
                          ↩️ استرجاع
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Warning */}
      <div className="mt-6 bg-red-50 p-4 rounded-lg border-r-4 border-red-500">
        <h3 className="font-bold text-red-700 mb-2">⚠️ تحذيرات مهمة:</h3>
        <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
          <li>استرجاع نسخة احتياطية سيحذف <strong>جميع البيانات الحالية</strong></li>
          <li>تأكد من إنشاء نسخة احتياطية حديثة قبل القيام بأي تغييرات كبيرة</li>
          <li>النسخ الاحتياطية لن يتم حذفها تلقائياً - احذفها يدوياً عند الحاجة</li>
          <li>لا يمكن التراجع عن عملية الاسترجاع بعد تنفيذها</li>
        </ul>
      </div>

      {/* Tips */}
      <div className="mt-4 bg-green-50 p-4 rounded-lg border-r-4 border-green-500">
        <h3 className="font-bold text-green-700 mb-2">💡 نصائح:</h3>
        <ul className="list-disc list-inside text-sm text-green-700 space-y-1">
          <li>النسخة الاحتياطية التلقائية تعمل يومياً الساعة 7:00 مساءً</li>
          <li>استخدم زر "تنزيل" لحفظ النسخة على جهازك</li>
          <li>يمكنك رفع النسخ المحفوظة يدوياً إلى Google Drive أو أي خدمة سحابية</li>
          <li>استخدم زر "استيراد نسخة" لرفع ملف نسخة احتياطية من جهازك</li>
          <li>احتفظ بنسخ احتياطية من فترات مختلفة للأمان</li>
          <li>حجم النسخة الاحتياطية صغير (عادة أقل من 1 MB)</li>
        </ul>
      </div>

      {/* Import Instructions */}
      <div className="mt-4 bg-blue-50 p-4 rounded-lg border-r-4 border-blue-500">
        <h3 className="font-bold text-blue-700 mb-2">📤 كيفية استيراد نسخة احتياطية:</h3>
        <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
          <li>اضغط على زر "استيراد نسخة"</li>
          <li>اختر ملف النسخة الاحتياطية (.json) من جهازك</li>
          <li>اختر الإجراء:
            <ul className="list-disc list-inside mr-6 mt-1">
              <li><strong>موافق</strong> = إضافة للقائمة فقط (آمن)</li>
              <li><strong>إلغاء</strong> = استرجاع مباشر (يحذف البيانات الحالية)</li>
            </ul>
          </li>
        </ol>
      </div>
    </div>
  );
};

// Users Management Component  
const Users = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'user'
  });
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    username: '',
    password: '',
    role: 'user'
  });
  const [companyInfo, setCompanyInfo] = useState({
    name: 'ماستر سيل',
    address: 'الحرفيين شارع السوبر جيت',
    phone: '01020630677'
  });
  const [editingCompany, setEditingCompany] = useState(false);
  const [selectedUserPermissions, setSelectedUserPermissions] = useState(null);

  const allPermissions = [
    { key: 'dashboard', label: 'لوحة التحكم' },
    { key: 'sales', label: 'المبيعات' },
    { key: 'inventory', label: 'المخزون' },
    { key: 'deferred', label: 'الآجل' },
    { key: 'expenses', label: 'المصروفات' },
    { key: 'revenue', label: 'الإيرادات' },
    { key: 'treasury', label: 'الخزينة' },
    { key: 'invoices', label: 'الفواتير' },
    { key: 'work-orders', label: 'أمر شغل' },
    { key: 'pricing', label: 'التسعير' },
    { key: 'users', label: 'إدارة المستخدمين' }
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);

      // Check if default users exist in database
      const dbUsers = response.data || [];
      const hasElsawy = dbUsers.some(user => user.username === 'Elsawy');
      const hasRoot = dbUsers.some(user => user.username === 'Root');

      // Create default users if they don't exist
      if (!hasElsawy) {
        await axios.post(`${API}/users`, {
          username: 'Elsawy',
          password: '100100',
          role: 'admin',
          permissions: allPermissions.map(p => p.key)
        });
      }

      if (!hasRoot) {
        await axios.post(`${API}/users`, {
          username: 'Root',
          password: 'master',
          role: 'user',
          permissions: ['dashboard', 'sales', 'inventory', 'deferred', 'expenses', 'treasury', 'work-orders']
        });
      }

      // Fetch users again if we created default users
      if (!hasElsawy || !hasRoot) {
        const updatedResponse = await axios.get(`${API}/users`);
        setUsers(updatedResponse.data || []);
      } else {
        setUsers(dbUsers);
      }

    } catch (error) {
      console.error('Error fetching users:', error);
      // Fall back to empty array for now
      setUsers([]);
    }
  };

  const addUser = async () => {
    if (!newUser.username || !newUser.password) {
      alert('الرجاء إدخال اسم المستخدم وكلمة المرور');
      return;
    }

    try {
      // Check if username already exists
      if (users.some(user => user.username === newUser.username)) {
        alert('اسم المستخدم موجود بالفعل');
        return;
      }

      // Default permissions based on role
      const defaultPermissions = newUser.role === 'admin'
        ? allPermissions.map(p => p.key)
        : ['dashboard', 'sales', 'inventory', 'deferred', 'expenses', 'treasury', 'work-orders', 'pricing'];

      // Let backend generate ID and created_at
      const user = {
        username: newUser.username,
        password: newUser.password,
        role: newUser.role,
        permissions: defaultPermissions
      };

      await axios.post(`${API}/users`, user);
      fetchUsers();
      setNewUser({ username: '', password: '', role: 'user' });
      alert('تم إضافة المستخدم بنجاح');
    } catch (error) {
      console.error('Error adding user:', error);
      alert('حدث خطأ في إضافة المستخدم: ' + (error.response?.data?.detail || error.message));
    }
  };

  const startEdit = (user) => {
    setEditingUser(user.id);
    setEditForm({
      username: user.username,
      password: '',
      role: user.role
    });
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setEditForm({ username: '', password: '', role: 'user' });
  };

  const saveEdit = async () => {
    if (!editForm.username) {
      alert('الرجاء إدخال اسم المستخدم');
      return;
    }

    // Check if username already exists (excluding current user)
    if (users.some(user => user.username === editForm.username && user.id !== editingUser)) {
      alert('اسم المستخدم موجود بالفعل');
      return;
    }

    try {
      // Find current user to preserve their permissions
      const currentUser = users.find(u => u.id === editingUser);
      if (!currentUser) {
        alert('المستخدم غير موجود');
        return;
      }

      // Update user in backend - preserve existing permissions
      const updatedUser = {
        id: editingUser,
        username: editForm.username,
        role: editForm.role,
        password: editForm.password || currentUser.password,
        permissions: currentUser.permissions || [],
        created_at: currentUser.created_at
      };

      await axios.put(`${API}/users/${editingUser}`, updatedUser);

      // Fetch updated data from database instead of updating local state
      fetchUsers();

      setEditingUser(null);
      setEditForm({ username: '', password: '', role: 'user' });
      alert('تم تحديث المستخدم بنجاح');
    } catch (error) {
      console.error('Error updating user:', error);
      alert('حدث خطأ في تحديث المستخدم: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteUser = async (userId) => {
    if (userId === '1' || userId === '2') {
      alert('لا يمكن حذف المستخدمين الأساسيين');
      return;
    }

    if (!confirm('هل أنت متأكد من حذف هذا المستخدم؟')) return;

    try {
      await axios.delete(`${API}/users/${userId}`);
      fetchUsers();
      alert('تم حذف المستخدم بنجاح');
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('حدث خطأ في حذف المستخدم');
    }
  };

  const resetPassword = async (userId) => {
    const newPassword = prompt('أدخل كلمة المرور الجديدة:');
    if (newPassword && newPassword.trim()) {
      try {
        // Find the user to get their current data
        const user = users.find(u => u.id === userId);
        if (!user) {
          alert('المستخدم غير موجود');
          return;
        }

        // Update password in backend
        const updatedUser = {
          id: user.id,
          username: user.username,
          password: newPassword.trim(),
          role: user.role,
          permissions: user.permissions || [],
          created_at: user.created_at
        };

        await axios.put(`${API}/users/${userId}`, updatedUser);
        alert('تم تحديث كلمة المرور بنجاح');
      } catch (error) {
        console.error('Error updating password:', error);
        alert('حدث خطأ في تحديث كلمة المرور: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const openPermissions = (user) => {
    setSelectedUserPermissions({
      ...user,
      tempPermissions: [...(user.permissions || [])]
    });
  };

  const togglePermission = (permissionKey) => {
    setSelectedUserPermissions(prev => {
      const newPermissions = prev.tempPermissions.includes(permissionKey)
        ? prev.tempPermissions.filter(p => p !== permissionKey)
        : [...prev.tempPermissions, permissionKey];

      return { ...prev, tempPermissions: newPermissions };
    });
  };

  const savePermissions = async () => {
    try {
      // Update permissions in backend
      const updatedUser = {
        id: selectedUserPermissions.id,
        username: selectedUserPermissions.username,
        password: selectedUserPermissions.password,
        role: selectedUserPermissions.role,
        permissions: selectedUserPermissions.tempPermissions,
        created_at: selectedUserPermissions.created_at
      };

      await axios.put(`${API}/users/${selectedUserPermissions.id}`, updatedUser);

      // Fetch updated data from database
      fetchUsers();

      setSelectedUserPermissions(null);
      alert('تم تحديث الصلاحيات بنجاح');
    } catch (error) {
      console.error('Error updating permissions:', error);
      alert('حدث خطأ في تحديث الصلاحيات: ' + (error.response?.data?.detail || error.message));
    }
  };

  const saveCompanyInfo = () => {
    setEditingCompany(false);
    alert('تم تحديث بيانات الشركة بنجاح');
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-blue-600 mb-4">إدارة المستخدمين</h2>

        <div className="flex space-x-4 space-x-reverse mb-4">
          <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
            حذف الكل
          </button>
          <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            إعادة تحميل
          </button>
          <button
            onClick={() => window.print()}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            طباعة تقرير
          </button>
        </div>
      </div>

      {/* Company Information */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">بيانات الشركة</h3>

        {editingCompany ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">اسم الشركة</label>
              <input
                type="text"
                value={companyInfo.name}
                onChange={(e) => setCompanyInfo({ ...companyInfo, name: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">العنوان</label>
              <input
                type="text"
                value={companyInfo.address}
                onChange={(e) => setCompanyInfo({ ...companyInfo, address: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">التليفون</label>
              <input
                type="text"
                value={companyInfo.phone}
                onChange={(e) => setCompanyInfo({ ...companyInfo, phone: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">اسم الشركة</label>
              <p className="p-2 bg-gray-100 rounded">{companyInfo.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">العنوان</label>
              <p className="p-2 bg-gray-100 rounded">{companyInfo.address}</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">التليفون</label>
              <p className="p-2 bg-gray-100 rounded">{companyInfo.phone}</p>
            </div>
          </div>
        )}

        <div className="flex space-x-4 space-x-reverse">
          {editingCompany ? (
            <>
              <button
                onClick={saveCompanyInfo}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                حفظ
              </button>
              <button
                onClick={() => setEditingCompany(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditingCompany(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              تعديل بيانات الشركة
            </button>
          )}
        </div>
      </div>

      {/* Add New User */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">إضافة مستخدم جديد</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">اسم المستخدم</label>
            <input
              type="text"
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="اسم المستخدم"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">كلمة المرور</label>
            <input
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="كلمة المرور"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">الصلاحية</label>
            <select
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              <option value="user">مستخدم عادي</option>
              <option value="admin">مدير</option>
            </select>
          </div>
        </div>

        <button
          onClick={addUser}
          className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600"
        >
          إضافة المستخدم
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">المستخدمين</h3>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">اسم المستخدم</th>
                <th className="border border-gray-300 p-2">الصلاحية</th>
                <th className="border border-gray-300 p-2">عدد الصلاحيات</th>
                <th className="border border-gray-300 p-2">تاريخ الإنشاء</th>
                <th className="border border-gray-300 p-2">الحالة</th>
                <th className="border border-gray-300 p-2">الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="border border-gray-300 p-2">
                    {editingUser === user.id ? (
                      <input
                        type="text"
                        value={editForm.username}
                        onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                        className="w-full p-1 border border-gray-300 rounded"
                      />
                    ) : (
                      <span className="font-semibold">{user.username}</span>
                    )}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {editingUser === user.id ? (
                      <select
                        value={editForm.role}
                        onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                        className="w-full p-1 border border-gray-300 rounded"
                      >
                        <option value="user">مستخدم عادي</option>
                        <option value="admin">مدير</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-1 rounded text-sm ${user.role === 'admin'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                        }`}>
                        {user.role === 'admin' ? 'مدير' : 'مستخدم عادي'}
                      </span>
                    )}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <span className="bg-gray-100 px-2 py-1 rounded text-sm">
                      {user.permissions?.length || 0} صلاحية
                    </span>
                  </td>
                  <td className="border border-gray-300 p-2">
                    {new Date(user.created_at).toLocaleDateString('ar-EG')}
                  </td>
                  <td className="border border-gray-300 p-2">
                    <span className="px-2 py-1 rounded text-sm bg-green-100 text-green-800">
                      نشط
                    </span>
                  </td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex space-x-2 space-x-reverse flex-wrap">
                      {editingUser === user.id ? (
                        <>
                          <button
                            onClick={saveEdit}
                            className="bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600 mb-1">
                            حفظ
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="bg-gray-500 text-white px-2 py-1 rounded text-sm hover:bg-gray-600 mb-1">
                            إلغاء
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => startEdit(user)}
                            className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600 mb-1">
                            تعديل
                          </button>
                          <button
                            onClick={() => openPermissions(user)}
                            className="bg-purple-500 text-white px-2 py-1 rounded text-sm hover:bg-purple-600 mb-1">
                            الصلاحيات
                          </button>
                          <button
                            onClick={() => resetPassword(user.id)}
                            className="bg-yellow-500 text-white px-2 py-1 rounded text-sm hover:bg-yellow-600 mb-1">
                            كلمة المرور
                          </button>
                          {(user.id !== '1' && user.id !== '2') && (
                            <button
                              onClick={() => deleteUser(user.id)}
                              className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600 mb-1">
                              حذف
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Permissions Modal */}
      {selectedUserPermissions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">
              صلاحيات المستخدم: {selectedUserPermissions.username}
            </h3>

            <div className="space-y-2 mb-4">
              {allPermissions.map(permission => (
                <label key={permission.key} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedUserPermissions.tempPermissions.includes(permission.key)}
                    onChange={() => togglePermission(permission.key)}
                    className="ml-2"
                  />
                  <span>{permission.label}</span>
                </label>
              ))}
            </div>

            <div className="flex space-x-4 space-x-reverse">
              <button
                onClick={savePermissions}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                حفظ
              </button>
              <button
                onClick={() => setSelectedUserPermissions(null)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Customer Management Component
const CustomerManagement = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [customers, setCustomers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});
  const [balances, setBalances] = useState({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCustomer, setNewCustomer] = useState({ name: '', phone: '', address: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data || []);
      // Fetch balances for all customers
      const balancePromises = (response.data || []).map(c =>
        axios.get(`${API}/customers/${c.id}/balance`).then(r => ({ id: c.id, ...r.data })).catch(() => ({ id: c.id, total_debt: 0, unpaid_invoices_count: 0 }))
      );
      const balanceResults = await Promise.all(balancePromises);
      const balanceMap = {};
      balanceResults.forEach(b => { balanceMap[b.id] = b; });
      setBalances(balanceMap);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
    setLoading(false);
  };

  const addCustomer = async () => {
    if (!newCustomer.name.trim()) {
      alert('الرجاء إدخال اسم العميل');
      return;
    }
    try {
      await axios.post(`${API}/customers`, newCustomer);
      alert('تم إضافة العميل بنجاح ✅');
      setNewCustomer({ name: '', phone: '', address: '' });
      setShowAddForm(false);
      fetchCustomers();
    } catch (error) {
      alert('خطأ: ' + (error.response?.data?.detail || error.message));
    }
  };

  const editDataRef = React.useRef(editData);
  React.useEffect(() => { editDataRef.current = editData; }, [editData]);

  const startEdit = (customer) => {
    const data = { name: customer.name, phone: customer.phone || '', address: customer.address || '' };
    setEditingId(customer.id);
    setEditData(data);
    editDataRef.current = data;
  };

  const saveEdit = async (customerId) => {
    const dataToSend = editDataRef.current;
    console.log('Saving customer:', customerId, 'Data:', dataToSend);
    try {
      await axios.put(`${API}/customers/${customerId}`, dataToSend);
      alert('تم تحديث بيانات العميل ✅');
      setEditingId(null);
      fetchCustomers();
    } catch (error) {
      alert('خطأ: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteCustomer = async (customerId, name) => {
    if (!window.confirm(`هل أنت متأكد من حذف العميل "${name}"؟`)) return;
    try {
      await axios.delete(`${API}/customers/${customerId}`);
      alert('تم حذف العميل ✅');
      fetchCustomers();
    } catch (error) {
      alert('خطأ: ' + (error.response?.data?.detail || error.message));
    }
  };

  const filteredCustomers = customers.filter(c =>
    c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.phone?.includes(searchTerm) ||
    c.address?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-blue-600">👥 إدارة العملاء</h2>
        <div className="flex gap-2">
          <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-bold">
            {customers.length} عميل
          </span>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 text-sm"
          >
            ➕ إضافة عميل
          </button>
        </div>
      </div>

      {/* Add Customer Form */}
      {showAddForm && (
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg mb-4">
          <h3 className="font-bold text-green-700 mb-3">إضافة عميل جديد</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="اسم العميل *"
              value={newCustomer.name}
              onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
              className="p-2 border border-gray-300 rounded-lg"
            />
            <input
              type="text"
              placeholder="رقم الهاتف"
              value={newCustomer.phone}
              onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
              className="p-2 border border-gray-300 rounded-lg"
            />
            <input
              type="text"
              placeholder="العنوان"
              value={newCustomer.address}
              onChange={(e) => setNewCustomer({ ...newCustomer, address: e.target.value })}
              className="p-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex gap-2 mt-3">
            <button onClick={addCustomer} className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 text-sm">حفظ</button>
            <button onClick={() => setShowAddForm(false)} className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 text-sm">إلغاء</button>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="🔍 بحث بالاسم أو الهاتف أو العنوان..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg text-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Customers Table */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">جاري التحميل...</div>
      ) : filteredCustomers.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {searchTerm ? 'لا توجد نتائج للبحث' : 'لا يوجد عملاء'}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-blue-50">
              <tr>
                <th className="p-3 text-right font-bold text-blue-700">#</th>
                <th className="p-3 text-right font-bold text-blue-700">الاسم</th>
                <th className="p-3 text-right font-bold text-blue-700">الهاتف</th>
                <th className="p-3 text-right font-bold text-blue-700">العنوان</th>
                <th className="p-3 text-right font-bold text-blue-700">المديونية</th>
                <th className="p-3 text-right font-bold text-blue-700">فواتير غير مدفوعة</th>
                <th className="p-3 text-center font-bold text-blue-700">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((customer, index) => {
                const balance = balances[customer.id] || {};
                const isEditing = editingId === customer.id;
                return (
                  <tr key={customer.id} className={`border-b hover:bg-gray-50 ${balance.total_debt > 0 ? 'bg-red-50' : ''}`}>
                    <td className="p-3 text-gray-500">{index + 1}</td>
                    <td className="p-3">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editData.name}
                          onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                          className="p-1 border border-blue-300 rounded w-full"
                        />
                      ) : (
                        <span className="font-bold">{customer.name}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editData.phone}
                          onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
                          className="p-1 border border-blue-300 rounded w-full"
                          dir="ltr"
                        />
                      ) : (
                        <span dir="ltr">{customer.phone || '—'}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editData.address}
                          onChange={(e) => setEditData({ ...editData, address: e.target.value })}
                          className="p-1 border border-blue-300 rounded w-full"
                        />
                      ) : (
                        <span>{customer.address || '—'}</span>
                      )}
                    </td>
                    <td className="p-3">
                      <span className={`font-bold ${balance.total_debt > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {(balance.total_debt || 0).toLocaleString()} {currency}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      {balance.unpaid_invoices_count > 0 ? (
                        <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-bold">
                          {balance.unpaid_invoices_count} فاتورة
                        </span>
                      ) : (
                        <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs">لا يوجد</span>
                      )}
                    </td>
                    <td className="p-3 text-center">
                      <div className="flex justify-center gap-1">
                        {isEditing ? (
                          <>
                            <button onClick={() => saveEdit(customer.id)} className="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600">حفظ</button>
                            <button onClick={() => setEditingId(null)} className="bg-gray-300 text-gray-700 px-2 py-1 rounded text-xs hover:bg-gray-400">إلغاء</button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => startEdit(customer)} className="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600">✏️ تعديل</button>
                            <button onClick={() => deleteCustomer(customer.id, customer.name)} className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600">🗑️ حذف</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      {customers.length > 0 && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-600">{customers.length}</div>
            <div className="text-sm text-gray-600">إجمالي العملاء</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-red-600">
              {Object.values(balances).reduce((sum, b) => sum + (b.total_debt || 0), 0).toLocaleString()} {currency}
            </div>
            <div className="text-sm text-gray-600">إجمالي المديونيات</div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-orange-600">
              {Object.values(balances).filter(b => b.total_debt > 0).length}
            </div>
            <div className="text-sm text-gray-600">عملاء عليهم مديونية</div>
          </div>
        </div>
      )}
    </div>
  );
};

// Material Pricing Component
const Pricing = () => {
  const { appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [materialPricings, setMaterialPricings] = useState([]);
  const [editingPricing, setEditingPricing] = useState(null);
  const [newPricing, setNewPricing] = useState({
    material_type: 'NBR',
    inner_diameter: '',
    outer_diameter: '',
    price_per_mm: '',
    manufacturing_cost_client1: '',
    manufacturing_cost_client2: '',
    manufacturing_cost_client3: '',
    notes: ''
  });

  const materialTypes = ['NBR', 'BUR', 'BT', 'VT', 'BOOM'];

  useEffect(() => {
    fetchMaterialPricings();
  }, []);

  const fetchMaterialPricings = async () => {
    try {
      const response = await axios.get(`${API}/material-pricing`);
      setMaterialPricings(response.data);
    } catch (error) {
      console.error('Error fetching material pricings:', error);
    }
  };

  const addMaterialPricing = async () => {
    if (!newPricing.inner_diameter || !newPricing.outer_diameter || !newPricing.price_per_mm) {
      alert('الرجاء إدخال جميع البيانات المطلوبة');
      return;
    }

    try {
      if (editingPricing) {
        // Update existing pricing
        await axios.put(`${API}/material-pricing/${editingPricing}`, {
          ...newPricing,
          inner_diameter: parseFloat(newPricing.inner_diameter),
          outer_diameter: parseFloat(newPricing.outer_diameter),
          price_per_mm: parseFloat(newPricing.price_per_mm),
          manufacturing_cost_client1: parseFloat(newPricing.manufacturing_cost_client1 || 0),
          manufacturing_cost_client2: parseFloat(newPricing.manufacturing_cost_client2 || 0),
          manufacturing_cost_client3: parseFloat(newPricing.manufacturing_cost_client3 || 0)
        });
        alert('تم تحديث التسعيرة بنجاح');
        setEditingPricing(null);
      } else {
        // Add new pricing
        await axios.post(`${API}/material-pricing`, {
          ...newPricing,
          inner_diameter: parseFloat(newPricing.inner_diameter),
          outer_diameter: parseFloat(newPricing.outer_diameter),
          price_per_mm: parseFloat(newPricing.price_per_mm),
          manufacturing_cost_client1: parseFloat(newPricing.manufacturing_cost_client1 || 0),
          manufacturing_cost_client2: parseFloat(newPricing.manufacturing_cost_client2 || 0),
          manufacturing_cost_client3: parseFloat(newPricing.manufacturing_cost_client3 || 0)
        });
        alert('تم إضافة التسعيرة بنجاح');
      }

      fetchMaterialPricings();
      setNewPricing({
        material_type: 'NBR',
        inner_diameter: '',
        outer_diameter: '',
        price_per_mm: '',
        manufacturing_cost_client1: '',
        manufacturing_cost_client2: '',
        manufacturing_cost_client3: '',
        notes: ''
      });
    } catch (error) {
      console.error('Error saving material pricing:', error);
      alert('حدث خطأ في حفظ التسعيرة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const editMaterialPricing = (pricing) => {
    setNewPricing({
      material_type: pricing.material_type,
      inner_diameter: pricing.inner_diameter.toString(),
      outer_diameter: pricing.outer_diameter.toString(),
      price_per_mm: pricing.price_per_mm.toString(),
      manufacturing_cost_client1: pricing.manufacturing_cost_client1.toString(),
      manufacturing_cost_client2: pricing.manufacturing_cost_client2.toString(),
      manufacturing_cost_client3: pricing.manufacturing_cost_client3.toString(),
      notes: pricing.notes || ''
    });
    setEditingPricing(pricing.id);
  };

  const deleteMaterialPricing = async (pricingId) => {
    if (!confirm('هل أنت متأكد من حذف هذه التسعيرة؟')) {
      return;
    }

    try {
      await axios.delete(`${API}/material-pricing/${pricingId}`);
      fetchMaterialPricings();
      alert('تم حذف التسعيرة بنجاح');
    } catch (error) {
      console.error('Error deleting material pricing:', error);
      alert('حدث خطأ في حذف التسعيرة: ' + (error.response?.data?.detail || error.message));
    }
  };

  const cancelEdit = () => {
    setEditingPricing(null);
    setNewPricing({
      material_type: 'NBR',
      inner_diameter: '',
      outer_diameter: '',
      price_per_mm: '',
      manufacturing_cost_client1: '',
      manufacturing_cost_client2: '',
      manufacturing_cost_client3: '',
      notes: ''
    });
  };

  const downloadPricingExcel = async () => {
    try {
      const response = await axios.get(`${API}/excel/export/material-pricing`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `material_pricing_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading pricing Excel:', error);
      alert('حدث خطأ في تحميل الملف: ' + (error.response?.data?.detail || error.message));
    }
  };

  const uploadPricingExcel = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/excel/import/material-pricing`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(`✅ ${response.data.message}`);
      if (response.data.errors && response.data.errors.length > 0) {
        alert('⚠️ أخطاء:\n' + response.data.errors.join('\n'));
      }
      fetchMaterialPricings();
    } catch (error) {
      console.error('Error uploading pricing Excel:', error);
      alert('حدث خطأ في رفع الملف: ' + (error.response?.data?.detail || error.message));
    }

    // Reset file input
    e.target.value = '';
  };

  return (
    <div className="p-6" dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-blue-600">💲 إدارة التسعير</h2>
        <div className="flex gap-2">
          <button
            onClick={downloadPricingExcel}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 flex items-center gap-2 text-sm"
          >
            📥 تحميل Excel
          </button>
          <label className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2 text-sm cursor-pointer">
            📤 رفع Excel
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={uploadPricingExcel}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Add/Edit Material Pricing Form */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">
          {editingPricing ? 'تعديل التسعيرة' : 'إضافة تسعيرة جديدة'}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">نوع الخامة</label>
            <select
              value={newPricing.material_type}
              onChange={(e) => setNewPricing({ ...newPricing, material_type: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
            >
              {materialTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الداخلي (مم)</label>
            <input
              type="number"
              step="0.1"
              value={newPricing.inner_diameter}
              onChange={(e) => setNewPricing({ ...newPricing, inner_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="القطر الداخلي"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">القطر الخارجي (مم)</label>
            <input
              type="number"
              step="0.1"
              value={newPricing.outer_diameter}
              onChange={(e) => setNewPricing({ ...newPricing, outer_diameter: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="القطر الخارجي"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">سعر الملي ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={newPricing.price_per_mm}
              onChange={(e) => setNewPricing({ ...newPricing, price_per_mm: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="سعر الملي الواحد"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">تكلفة التصنيع - عميل 1 ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={newPricing.manufacturing_cost_client1}
              onChange={(e) => setNewPricing({ ...newPricing, manufacturing_cost_client1: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="تكلفة التصنيع للعميل 1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">تكلفة التصنيع - عميل 2 ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={newPricing.manufacturing_cost_client2}
              onChange={(e) => setNewPricing({ ...newPricing, manufacturing_cost_client2: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="تكلفة التصنيع للعميل 2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">تكلفة التصنيع - عميل 3 ({currency})</label>
            <input
              type="number"
              step="0.01"
              value={newPricing.manufacturing_cost_client3}
              onChange={(e) => setNewPricing({ ...newPricing, manufacturing_cost_client3: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="تكلفة التصنيع للعميل 3"
            />
          </div>

          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium mb-1">ملاحظات</label>
            <textarea
              value={newPricing.notes}
              onChange={(e) => setNewPricing({ ...newPricing, notes: e.target.value })}
              className="w-full p-2 border border-gray-300 rounded"
              rows="2"
              placeholder="ملاحظات إضافية..."
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4 space-x-reverse mt-4">
          {editingPricing && (
            <button
              onClick={cancelEdit}
              className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600"
            >
              إلغاء
            </button>
          )}
          <button
            onClick={addMaterialPricing}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
          >
            {editingPricing ? 'تحديث التسعيرة' : 'إضافة التسعيرة'}
          </button>
        </div>
      </div>

      {/* Material Pricings Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">قائمة التسعيرات</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">نوع الخامة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الأبعاد (داخلي×خارجي)</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">سعر الملي</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">عميل 1</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">عميل 2</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">عميل 3</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ملاحظات</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">العمليات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {materialPricings.map((pricing, index) => (
                <tr key={pricing.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {pricing.material_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.inner_diameter}×{pricing.outer_diameter} مم
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.price_per_mm.toFixed(2)} {currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.manufacturing_cost_client1.toFixed(2)} {currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.manufacturing_cost_client2.toFixed(2)} {currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.manufacturing_cost_client3.toFixed(2)} {currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pricing.notes || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => editMaterialPricing(pricing)}
                      className="text-blue-600 hover:text-blue-900 ml-2"
                    >
                      تعديل
                    </button>
                    <button
                      onClick={() => deleteMaterialPricing(pricing.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      حذف
                    </button>
                  </td>
                </tr>
              ))}

              {materialPricings.length === 0 && (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                    لا توجد تسعيرات مضافة
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Main Treasury Component - الخزنة الرئيسية
const MainTreasury = () => {
  const { user, appSettings } = useAuth();
  const currency = appSettings?.currency || 'ج.م';
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [transactionType, setTransactionType] = useState('deposit');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [reference, setReference] = useState('');
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Verify password
  const verifyPassword = async () => {
    try {
      const response = await axios.post(`${API}/main-treasury/verify-password`, {
        password: password
      });

      if (response.data.success) {
        setIsAuthenticated(true);
        fetchMainTreasuryData();
      } else {
        alert('كلمة المرور غير صحيحة');
        setPassword('');
      }
    } catch (error) {
      console.error('Error verifying password:', error);
      alert('حدث خطأ في التحقق من كلمة المرور');
    }
  };

  // Fetch main treasury data
  const fetchMainTreasuryData = async () => {
    try {
      const balanceResponse = await axios.get(`${API}/main-treasury/balance`);
      setBalance(balanceResponse.data.balance);

      const transactionsResponse = await axios.get(`${API}/main-treasury/transactions`);
      setTransactions(transactionsResponse.data);
    } catch (error) {
      console.error('Error fetching main treasury data:', error);
    }
  };

  // Handle transaction (deposit or withdrawal)
  const handleTransaction = async () => {
    if (!amount || !description) {
      alert('الرجاء إدخال المبلغ والوصف');
      return;
    }

    if (parseFloat(amount) <= 0) {
      alert('الرجاء إدخال مبلغ صحيح');
      return;
    }

    try {
      const endpoint = transactionType === 'deposit'
        ? `${API}/main-treasury/deposit?username=${user.username}`
        : `${API}/main-treasury/withdrawal?username=${user.username}`;

      await axios.post(endpoint, {
        transaction_type: transactionType,
        amount: parseFloat(amount),
        description: description,
        reference: reference || null
      });

      alert(transactionType === 'deposit' ? 'تم الإيداع بنجاح' : 'تم الصرف بنجاح');

      // Reset form
      setAmount('');
      setDescription('');
      setReference('');

      // Refresh data
      fetchMainTreasuryData();
    } catch (error) {
      console.error('Error performing transaction:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في العملية');
    }
  };

  // Change password
  const changePassword = async () => {
    if (!oldPassword || !newPassword) {
      alert('الرجاء إدخال كلمة المرور القديمة والجديدة');
      return;
    }

    if (newPassword.length < 4) {
      alert('كلمة المرور يجب أن تكون 4 أرقام على الأقل');
      return;
    }

    try {
      await axios.post(`${API}/main-treasury/change-password`, {
        old_password: oldPassword,
        new_password: newPassword
      });

      alert('تم تغيير كلمة المرور بنجاح');
      setShowPasswordChange(false);
      setOldPassword('');
      setNewPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في تغيير كلمة المرور');
    }
  };

  // If not authenticated, show password screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 p-6" dir="rtl">
        <div className="bg-white p-8 rounded-lg shadow-2xl max-w-md w-full">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🔐</div>
            <h2 className="text-2xl font-bold text-gray-800">الخزنة الرئيسية</h2>
            <p className="text-gray-600 mt-2">الرجاء إدخال كلمة المرور للدخول</p>
          </div>

          <div className="space-y-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && verifyPassword()}
              placeholder="كلمة المرور"
              className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center text-lg"
              autoFocus
            />

            <button
              onClick={verifyPassword}
              className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 font-semibold text-lg transition-colors"
            >
              دخول
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main treasury interface
  return (
    <div className="p-6 bg-gray-50 min-h-screen" dir="rtl">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
              🔐 الخزنة الرئيسية
            </h1>
            <p className="text-gray-600 mt-2">إدارة الخزنة الرئيسية للشركة</p>
          </div>
          <div className="text-left">
            <p className="text-sm text-gray-500">الرصيد الحالي</p>
            <p className="text-4xl font-bold text-green-600">
              {balance.toFixed(2)} {currency}
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Deposit/Withdrawal Form */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            {transactionType === 'deposit' ? '💵 إيداع' : '💸 صرف'}
          </h3>

          <div className="space-y-4">
            {/* Transaction Type Toggle */}
            <div className="flex gap-2">
              <button
                onClick={() => setTransactionType('deposit')}
                className={`flex-1 py-2 rounded-lg font-semibold transition-colors ${transactionType === 'deposit'
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
              >
                💵 إيداع
              </button>
              <button
                onClick={() => setTransactionType('withdrawal')}
                className={`flex-1 py-2 rounded-lg font-semibold transition-colors ${transactionType === 'withdrawal'
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
              >
                💸 صرف
              </button>
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                المبلغ ({currency})
              </label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                الوصف/السبب *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="اكتب سبب الإيداع أو الصرف..."
                rows="3"
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Reference (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                المرجع (اختياري)
              </label>
              <input
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                placeholder="رقم المستند أو المرجع"
                className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Submit Button */}
            <button
              onClick={handleTransaction}
              className={`w-full py-3 rounded-lg font-semibold text-white transition-colors ${transactionType === 'deposit'
                ? 'bg-green-500 hover:bg-green-600'
                : 'bg-red-500 hover:bg-red-600'
                }`}
            >
              {transactionType === 'deposit' ? '✅ تأكيد الإيداع' : '✅ تأكيد الصرف'}
            </button>
          </div>
        </div>

        {/* Password Change */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            🔑 إدارة كلمة المرور
          </h3>

          {!showPasswordChange ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">تغيير كلمة مرور الخزنة الرئيسية</p>
              <button
                onClick={() => setShowPasswordChange(true)}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 font-semibold"
              >
                تغيير كلمة المرور
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  كلمة المرور القديمة
                </label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  كلمة المرور الجديدة
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={changePassword}
                  className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 font-semibold"
                >
                  ✅ تأكيد التغيير
                </button>
                <button
                  onClick={() => {
                    setShowPasswordChange(false);
                    setOldPassword('');
                    setNewPassword('');
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-400 font-semibold"
                >
                  ❌ إلغاء
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Transactions History */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          📋 سجل الحركات
        </h3>

        {transactions.length === 0 ? (
          <p className="text-center text-gray-500 py-8">لا توجد حركات مسجلة</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-3 text-right">التاريخ</th>
                  <th className="border border-gray-300 p-3 text-right">نوع العملية</th>
                  <th className="border border-gray-300 p-3 text-right">المبلغ</th>
                  <th className="border border-gray-300 p-3 text-right">الوصف</th>
                  <th className="border border-gray-300 p-3 text-right">المرجع</th>
                  <th className="border border-gray-300 p-3 text-right">الرصيد بعد</th>
                  <th className="border border-gray-300 p-3 text-right">نفذ بواسطة</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="border border-gray-300 p-3">
                      {new Date(transaction.date).toLocaleDateString('ar-EG', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="border border-gray-300 p-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${transaction.transaction_type === 'deposit'
                        ? 'bg-green-100 text-green-800'
                        : transaction.transaction_type === 'withdrawal'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-blue-100 text-blue-800'
                        }`}>
                        {transaction.transaction_type === 'deposit'
                          ? '💵 إيداع'
                          : transaction.transaction_type === 'withdrawal'
                            ? '💸 صرف'
                            : '↔️ ترحيل'}
                      </span>
                    </td>
                    <td className={`border border-gray-300 p-3 font-bold ${transaction.transaction_type === 'withdrawal'
                      ? 'text-red-600'
                      : 'text-green-600'
                      }`}>
                      {transaction.transaction_type === 'withdrawal' ? '-' : '+'}
                      {transaction.amount.toFixed(2)} {currency}
                    </td>
                    <td className="border border-gray-300 p-3">{transaction.description}</td>
                    <td className="border border-gray-300 p-3 text-gray-600">
                      {transaction.reference || '-'}
                    </td>
                    <td className="border border-gray-300 p-3 font-bold text-blue-600">
                      {transaction.balance_after.toFixed(2)} {currency}
                    </td>
                    <td className="border border-gray-300 p-3">{transaction.performed_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// Settings Component (الضبط)
const Settings = () => {
  const { fetchAppSettings } = useAuth();
  const [settings, setSettings] = useState({
    company_name: 'ماستر سيل',
    company_name_full: 'شركة ماستر سيل',
    company_subtitle: 'تصنيع جميع أنواع الأويل سيل',
    company_details_1: 'جميع الأقطار حتى ٥٠٠مل',
    company_details_2: 'هيدروليك - نيوماتيك',
    company_address: 'الحرفيين - السلام - أمام السوبر جيت',
    company_phone: '٠١٠٢٠٦٣٠٦٧٧',
    company_mobile: '٠١٠٢٠٦٣٠٦٧٧ - ٠١٠٦٢٣٩٠٨٧٠',
    company_landline: '٠١٠٢٠٦٣٠٦٧٧',
    logo_url: '',
    system_subtitle: 'نظام إدارة متكامل',
    currency: 'ج.م',
    invoice_language: 'ar',
    company_name_full_en: '',
    company_subtitle_en: '',
    company_details_1_en: '',
    company_details_2_en: '',
    company_address_en: '',
    company_mobile_en: '',
    company_landline_en: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(prev => ({ ...prev, ...response.data }));
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, settings);
      // Refresh global app settings (currency, language)
      if (fetchAppSettings) fetchAppSettings();
      alert('تم حفظ الإعدادات بنجاح ✅');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('حدث خطأ في حفظ الإعدادات');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const [uploadingLogo, setUploadingLogo] = useState(false);

  const uploadLogo = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('الرجاء اختيار ملف صورة فقط');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('حجم الملف كبير جداً (الحد الأقصى 5 ميجابايت)');
      return;
    }

    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post(`${API}/settings/logo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setSettings(prev => ({ ...prev, logo_url: response.data.logo_url }));
      alert('تم رفع اللوجو بنجاح ✅');
    } catch (error) {
      console.error('Error uploading logo:', error);
      alert('حدث خطأ في رفع اللوجو');
    } finally {
      setUploadingLogo(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-500">⏳ جاري التحميل...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">⚙️ الضبط - إعدادات الشركة</h2>
        <button
          onClick={saveSettings}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-semibold shadow-lg transition-all"
        >
          {saving ? '⏳ جاري الحفظ...' : '💾 حفظ الإعدادات'}
        </button>
      </div>

      {/* Company Identity */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-blue-700 mb-4 border-b pb-2">🏢 هوية الشركة</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اسم الشركة (الشريط الجانبي)</label>
            <input
              type="text"
              value={settings.company_name}
              onChange={(e) => handleChange('company_name', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="ماستر سيل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اسم الشركة الكامل (الفاتورة)</label>
            <input
              type="text"
              value={settings.company_name_full}
              onChange={(e) => handleChange('company_name_full', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="شركة ماستر سيل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">الوصف الفرعي (الشريط الجانبي)</label>
            <input
              type="text"
              value={settings.system_subtitle}
              onChange={(e) => handleChange('system_subtitle', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="نظام إدارة متكامل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اللوجو</label>
            <div className="flex items-center gap-3">
              <label className="cursor-pointer bg-blue-50 hover:bg-blue-100 text-blue-700 border-2 border-dashed border-blue-300 rounded-lg p-3 flex items-center gap-2 transition-all w-full justify-center">
                <span className="text-2xl">📤</span>
                <span className="font-medium">{uploadingLogo ? 'جاري الرفع...' : 'اختر صورة اللوجو'}</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={uploadLogo}
                  className="hidden"
                  disabled={uploadingLogo}
                />
              </label>
            </div>
            <p className="text-xs text-gray-400 mt-1">الحد الأقصى 5 ميجابايت (PNG, JPG, SVG)</p>
          </div>
        </div>

        {/* Logo Preview */}
        {settings.logo_url && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg flex items-center gap-4">
            <img
              src={settings.logo_url}
              alt="Logo Preview"
              className="h-16 w-16 rounded-lg object-cover border"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
            <div>
              <p className="text-sm text-gray-600 font-medium">اللوجو الحالي</p>
              <button
                onClick={() => handleChange('logo_url', '')}
                className="text-xs text-red-500 hover:text-red-700 mt-1"
              >🗑️ حذف اللوجو</button>
            </div>
          </div>
        )}
      </div>

      {/* Invoice Details */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-green-700 mb-4 border-b pb-2">🧾 بيانات الفاتورة</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">وصف النشاط (سطر 1)</label>
            <input
              type="text"
              value={settings.company_subtitle}
              onChange={(e) => handleChange('company_subtitle', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="تصنيع جميع أنواع الأويل سيل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">وصف النشاط (سطر 2)</label>
            <input
              type="text"
              value={settings.company_details_1}
              onChange={(e) => handleChange('company_details_1', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="جميع الأقطار حتى ٥٠٠مل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">وصف النشاط (سطر 3)</label>
            <input
              type="text"
              value={settings.company_details_2}
              onChange={(e) => handleChange('company_details_2', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="هيدروليك - نيوماتيك"
            />
          </div>
        </div>
      </div>

      {/* Contact Info */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-purple-700 mb-4 border-b pb-2">📞 بيانات الاتصال</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">العنوان</label>
            <input
              type="text"
              value={settings.company_address}
              onChange={(e) => handleChange('company_address', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="العنوان الكامل"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">أرقام الموبايل (الفاتورة)</label>
            <input
              type="text"
              value={settings.company_mobile}
              onChange={(e) => handleChange('company_mobile', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="٠١٠٢٠٦٣٠٦٧٧ - ٠١٠٦٢٣٩٠٨٧٠"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رقم التليفون (الفاتورة)</label>
            <input
              type="text"
              value={settings.company_landline}
              onChange={(e) => handleChange('company_landline', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="٠١٠٢٠٦٣٠٦٧٧"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف (الشريط الجانبي)</label>
            <input
              type="text"
              value={settings.company_phone}
              onChange={(e) => handleChange('company_phone', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="٠١٠٢٠٦٣٠٦٧٧"
            />
          </div>
        </div>
      </div>

      {/* English Company Info for Invoice */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-indigo-700 mb-4 border-b pb-2">🌐 Company Info (English) - بيانات الشركة بالإنجليزية</h3>
        <p className="text-sm text-gray-500 mb-4">هذه البيانات تظهر في الفاتورة عند اختيار اللغة الإنجليزية</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company Name (Full)</label>
            <input
              type="text"
              value={settings.company_name_full_en}
              onChange={(e) => handleChange('company_name_full_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Faster Seal Co."
              dir="ltr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Business Description (Line 1)</label>
            <input
              type="text"
              value={settings.company_subtitle_en}
              onChange={(e) => handleChange('company_subtitle_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Manufacturing All Types of Oil Seals"
              dir="ltr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Business Description (Line 2)</label>
            <input
              type="text"
              value={settings.company_details_1_en}
              onChange={(e) => handleChange('company_details_1_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="All Diameters up to 500mm"
              dir="ltr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Business Description (Line 3)</label>
            <input
              type="text"
              value={settings.company_details_2_en}
              onChange={(e) => handleChange('company_details_2_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Hydraulic - Pneumatic"
              dir="ltr"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              type="text"
              value={settings.company_address_en}
              onChange={(e) => handleChange('company_address_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Al-Herafeyeen - Al-Salam"
              dir="ltr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Numbers</label>
            <input
              type="text"
              value={settings.company_mobile_en}
              onChange={(e) => handleChange('company_mobile_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="01020630677 - 01062390870"
              dir="ltr"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="text"
              value={settings.company_landline_en}
              onChange={(e) => handleChange('company_landline_en', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="01020630677"
              dir="ltr"
            />
          </div>
        </div>
      </div>

      {/* Currency & Invoice Language */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-amber-700 mb-4 border-b pb-2">💱 إعدادات العملة ولغة الفاتورة</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">العملة</label>
            <select
              value={['ج.م', '$', '€', '£', 'ر.س', 'د.إ', 'د.ك', 'ر.ع', 'د.ب', 'ل.ل', 'ر.ق'].includes(settings.currency) ? settings.currency : '_custom'}
              onChange={(e) => {
                if (e.target.value !== '_custom') {
                  handleChange('currency', e.target.value);
                }
              }}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-lg"
            >
              <option value="ج.م">ج.م - جنيه مصري</option>
              <option value="$">$ - دولار أمريكي</option>
              <option value="€">€ - يورو</option>
              <option value="£">£ - جنيه إسترليني</option>
              <option value="ر.س">ر.س - ريال سعودي</option>
              <option value="د.إ">د.إ - درهم إماراتي</option>
              <option value="د.ك">د.ك - دينار كويتي</option>
              <option value="ر.ع">ر.ع - ريال عماني</option>
              <option value="د.ب">د.ب - دينار بحريني</option>
              <option value="ل.ل">ل.ل - ليرة لبنانية</option>
              <option value="ر.ق">ر.ق - ريال قطري</option>
              <option value="_custom">أخرى (مخصص)</option>
            </select>
            {!['ج.م', '$', '€', '£', 'ر.س', 'د.إ', 'د.ك', 'ر.ع', 'د.ب', 'ل.ل', 'ر.ق'].includes(settings.currency) && (
              <input
                type="text"
                value={settings.currency}
                onChange={(e) => handleChange('currency', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg mt-2 focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                placeholder="أدخل رمز العملة المخصص"
              />
            )}
            <div className="mt-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-sm text-amber-800">
                <strong>العملة الحالية:</strong> <span className="text-2xl font-bold">{settings.currency}</span>
              </p>
              <p className="text-xs text-amber-600 mt-1">ستظهر هذه العملة في جميع أنحاء الموقع والفواتير</p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">لغة الفاتورة</label>
            <div className="flex gap-3">
              <button
                onClick={() => handleChange('invoice_language', 'ar')}
                className={`flex-1 p-4 rounded-xl border-2 transition-all text-center ${settings.invoice_language === 'ar'
                  ? 'border-amber-500 bg-amber-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
              >
                <div className="text-3xl mb-2">🇪🇬</div>
                <div className="font-bold text-lg">العربية</div>
                <div className="text-xs text-gray-500 mt-1">فاتورة - عرض سعر</div>
              </button>
              <button
                onClick={() => handleChange('invoice_language', 'en')}
                className={`flex-1 p-4 rounded-xl border-2 transition-all text-center ${settings.invoice_language === 'en'
                  ? 'border-amber-500 bg-amber-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
              >
                <div className="text-3xl mb-2">🇬🇧</div>
                <div className="font-bold text-lg">English</div>
                <div className="text-xs text-gray-500 mt-1">Invoice - Quotation</div>
              </button>
            </div>
            <div className="mt-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-xs text-amber-600">لغة الفاتورة تؤثر فقط على طباعة الفاتورة، واجهة الموقع تبقى بالعربية</p>
            </div>
          </div>
        </div>
      </div>

      {/* Preview */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-bold text-orange-700 mb-4 border-b pb-2">👁️ معاينة رأس الفاتورة</h3>
        <div className="border-2 border-gray-300 rounded-lg p-6 bg-gray-50" dir="rtl">
          <div className="flex justify-between items-start">
            <div className="text-right">
              <h2 className="text-2xl font-bold text-blue-900">{settings.company_name_full}</h2>
              <p className="text-sm text-gray-600">{settings.company_subtitle}</p>
              <p className="text-sm text-gray-500">{settings.company_details_1}</p>
              <p className="text-sm text-gray-500">{settings.company_details_2}</p>
            </div>
            <div className="text-center">
              {settings.logo_url && (
                <img src={settings.logo_url} alt="Logo" className="h-20 w-auto mx-auto mb-2 rounded" />
              )}
            </div>
          </div>
          <hr className="my-3 border-gray-400" />
          <div className="flex justify-between text-sm text-gray-700">
            <div>
              <p>موبايل: {settings.company_mobile}</p>
              <p>تليفون: {settings.company_landline}</p>
            </div>
            <div className="text-left">
              <p>{settings.company_address}</p>
              <p>موبايل: {settings.company_mobile}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button Bottom */}
      <div className="text-center mb-8">
        <button
          onClick={saveSettings}
          disabled={saving}
          className="bg-green-600 text-white px-10 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 font-bold text-lg shadow-lg transition-all"
        >
          {saving ? '⏳ جاري الحفظ...' : '💾 حفظ جميع الإعدادات'}
        </button>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentPage, setCurrentPage] = useState('sales'); // Default to sales instead of dashboard
  const { user } = useAuth();

  if (!user) return <Login />;

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (user?.role === 'admin' || user?.role === 'master' || user?.username === 'Elsawy') ? <Dashboard /> : <Sales />;
      case 'daily-sales': return <DailySalesReport />;
      case 'sales': return <Sales />;
      case 'inventory': return <Inventory />;
      case 'stock': return <Stock />;
      case 'local': return <Local />;
      case 'deferred': return <Deferred />;
      case 'expenses': return <Expenses />;
      case 'revenue': return <Revenue />;
      case 'treasury': return <Treasury />;
      case 'main-treasury':
        return (user?.role === 'admin' || user?.role === 'master' || user?.username === 'Elsawy') ? <MainTreasury /> : <Sales />;
      case 'invoices': return <Invoices />;
      case 'deleted-invoices': return <DeletedInvoices />;
      case 'customer-statement': return <CustomerStatement />;
      case 'settle-account': return <SettleAccount />;
      case 'work-orders': return <WorkOrders />;
      case 'pricing': return <Pricing />;
      case 'customers': return <CustomerManagement />;
      case 'backup': return <Backup />;
      case 'users': return <Users />;
      case 'settings': return <Settings />;
      default: return <Sales />; // Default to sales instead of dashboard
    }
  };

  return (
    <div className="flex h-screen bg-gray-50" dir="rtl">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="p-6">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};

// Root App with AuthProvider
const AppWithAuth = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default AppWithAuth;