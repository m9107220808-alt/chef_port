#!/usr/bin/env python3
"""
Полное исправление админки - все фичи сразу
"""
import re

file_path = "/root/chefport-bot/web/miniapp_admin.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. УМЕНЬШАЕМ МОДАЛЬНОЕ ОКНО НА 20%
content = content.replace('max-width: 600px;', 'max-width: 480px;')
content = content.replace('max-height: 90vh;', 'max-height: 72vh;')

# 2. ИСПРАВЛЯЕМ ФУНКЦИЮ СОХРАНЕНИЯ
old_save = r'async function saveProduct\(e\) \{[^}]+\}[^}]+\}'
new_save = '''async function saveProduct(e) {
            e.preventDefault();
            const data = {
                name: document.getElementById('p-name').value,
                priceperkg: parseFloat(document.getElementById('p-price').value),
                description: document.getElementById('p-desc').value || '',
                categoryid: parseInt(document.getElementById('p-cat').value),
                in_stock: document.getElementById('p-stock').checked,
                is_hit: document.getElementById('p-hit').checked,
                is_discount: document.getElementById('p-is-discount')?.checked || false,
                discount_percent: parseInt(document.getElementById('p-discount-percent')?.value || 0),
                image_url: document.getElementById('p-image-url')?.value || null
            };

            try {
                const method = editingId ? 'PATCH' : 'POST';
                const url = editingId ? API_BASE + '/products/' + editingId : API_BASE + '/products';
                
                const r = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (r.ok) {
                    closeModal();
                    await loadProducts();
                } else {
                    alert('Ошибка сохранения');
                }
            } catch (e) { 
                console.error(e); 
                alert('Ошибка сети');
            }
        }'''

content = re.sub(old_save, new_save, content, flags=re.DOTALL)

# 3. ДОБАВЛЯЕМ БЫСТРОЕ РЕДАКТИРОВАНИЕ В СПИСОК ТОВАРОВ
# Найдем renderProducts и обновим HTML карточки
old_card = r'<div class="prod-meta">\$\{Math\.round\(p\.priceperkg\)\} ₽ \$\{p\.is_weighted \? \'/ кг\' : \'/ шт\'\} • \$\{p\.code \|\| \'\'\}</div>'
new_card = '''<div class="prod-meta" style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:4px;">
                            <input type="number" value="${p.priceperkg||0}" 
                                style="width:70px;padding:4px;border:1px solid #444;border-radius:4px;background:#2a2a2a;color:#fff;font-size:12px;"
                                onchange="quickUpdate(${p.id}, 'priceperkg', this.value)" 
                                onclick="event.stopPropagation()">
                            <span style="font-size:11px;color:#888;">${p.is_weighted ? '/ кг' : '/ шт'}</span>
                            <label style="cursor:pointer;" title="Хит">
                                <input type="checkbox" ${p.is_hit ? 'checked' : ''} 
                                    style="display:none"
                                    onchange="quickUpdate(${p.id}, 'is_hit', this.checked)"
                                    onclick="event.stopPropagation()">
                                <span style="font-size:16px;opacity:${p.is_hit ? '1' : '0.3'};">🔥</span>
                            </label>
                            <label style="cursor:pointer;" title="Скидка">
                                <input type="checkbox" ${p.is_discount ? 'checked' : ''} 
                                    style="display:none"
                                    onchange="quickUpdate(${p.id}, 'is_discount', this.checked)"
                                    onclick="event.stopPropagation()">
                                <span style="font-size:16px;opacity:${p.is_discount ? '1' : '0.3'};">🏷️</span>
                            </label>
                        </div>'''

content = re.sub(old_card, new_card, content)

# 4. ДОБАВЛЯЕМ ФУНКЦИЮ БЫСТРОГО ОБНОВЛЕНИЯ
quick_func = '''
        async function quickUpdate(id, field, value) {
            try {
                const body = {};
                if (field === 'is_hit' || field === 'is_discount') {
                    body[field] = value;
                } else {
                    body[field] = parseFloat(value);
                }
                
                const res = await fetch(API_BASE + '/products/' + id, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                
                if (res.ok) {
                    await loadProducts();
                }
            } catch (err) {
                console.error(err);
            }
        }

'''

# Вставляем перед renderProducts
if 'quickUpdate' not in content:
    content = content.replace('function renderProducts(list)', quick_func + '        function renderProducts(list)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Admin panel fully updated!")
