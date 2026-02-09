#!/usr/bin/env python3
"""
Добавляет функционал быстрого редактирования в админку
"""
import re

admin_file = "/root/chefport-bot/web/miniapp_admin.html"

with open(admin_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Обновляем renderProducts для добавления инлайн-контролов
old_render = r'function renderProducts\(list\) \{[^}]+\}'
new_render = '''function renderProducts(list) {
            const container = document.getElementById('products-list');
            if (!list.length) {
                container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-secondary)">Нет товаров</div>';
                return;
            }

            const html = list.map(p => `
                <div class="product-card" onclick="openProductModal(${p.id})">
                    <div class="product-img" style="background-image:url('${p.image_url || ''}')"></div>
                    <div class="product-info">
                        <div class="product-name">${p.name}</div>
                        <div class="product-meta">
                            <div class="quick-edit-controls" onclick="event.stopPropagation()">
                                <input type="number" class="quick-price" value="${p.priceperkg || 0}" 
                                    onchange="quickUpdateProduct(${p.id}, 'priceperkg', this.value)" 
                                    onclick="event.stopPropagation()" step="0.01" min="0">
                                <label class="quick-toggle">
                                    <input type="checkbox" ${p.is_hit ? 'checked' : ''} 
                                        onchange="quickUpdateProduct(${p.id}, 'is_hit', this.checked)"
                                        onclick="event.stopPropagation()">
                                    <span>🔥</span>
                                </label>
                                <label class="quick-toggle">
                                    <input type="checkbox" ${p.is_discount ? 'checked' : ''} 
                                        onchange="quickUpdateProduct(${p.id}, 'is_discount', this.checked)"
                                        onclick="event.stopPropagation()">
                                    <span>🏷️</span>
                                </label>
                                ${p.is_discount ? `<select class="quick-discount" onchange="quickUpdateProduct(${p.id}, 'discount_percent', this.value)" onclick="event.stopPropagation()">
                                    <option value="5" ${p.discount_percent == 5 ? 'selected' : ''}>5%</option>
                                    <option value="10" ${p.discount_percent == 10 ? 'selected' : ''}>10%</option>
                                    <option value="15" ${p.discount_percent == 15 ? 'selected' : ''}>15%</option>
                                    <option value="20" ${p.discount_percent == 20 ? 'selected' : ''}>20%</option>
                                    <option value="25" ${p.discount_percent == 25 ? 'selected' : ''}>25%</option>
                                    <option value="30" ${p.discount_percent == 30 ? 'selected' : ''}>30%</option>
                                </select>` : ''}
                            </div>
                        </div>
                    </div>
                    <button class="btn-icon btn-edit">✎</button>
                </div>
            `).join('');

            container.innerHTML = html;
        }'''

# Находим и заменяем функцию renderProducts
pattern = r'function renderProducts\(list\) \{[^}]+container\.innerHTML = html;[^}]+\}'
content = re.sub(pattern, new_render, content, flags=re.DOTALL)

# 2. Добавляем функцию быстрого обновления
quick_update_func = '''
        // Quick update product field
        async function quickUpdateProduct(id, field, value) {
            try {
                const body = { [field]: field === 'is_hit' || field === 'is_discount' ? value : (field === 'discount_percent' ? parseInt(value) : parseFloat(value)) };
                const res = await fetch(API_BASE + '/products/' + id, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                if (res.ok) {
                    await loadProducts();
                    console.log(`✅ Updated ${field} for product ${id}`);
                } else {
                    alert('Ошибка обновления');
                }
            } catch (err) {
                console.error(err);
                alert('Ошибка сети');
            }
        }
'''

# Вставляем перед функцией renderProducts
content = content.replace('function renderProducts(list)', quick_update_func + '\n        function renderProducts(list)')

# 3. Добавляем CSS для быстрых контролов
quick_edit_css = '''
        .quick-edit-controls {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 8px;
            padding: 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .quick-price {
            width: 80px;
            padding: 4px 8px;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text);
            font-size: 14px;
        }
        .quick-toggle {
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        .quick-toggle input {
            display: none;
        }
        .quick-toggle span {
            font-size: 18px;
            opacity: 0.3;
            transition: opacity 0.2s;
        }
        .quick-toggle input:checked + span {
            opacity: 1;
        }
        .quick-discount {
            padding: 4px;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text);
            font-size: 12px;
        }
'''

# Вставляем CSS перед закрытием </style>
content = content.replace('</style>', quick_edit_css + '\n    </style>')

# Сохраняем
with open(admin_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Admin panel updated with quick edit features!")
