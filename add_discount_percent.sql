-- Добавляем поле discount_percent к таблице products
ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_percent INTEGER DEFAULT 0;

-- Обновляем существующие записи
UPDATE products SET discount_percent = 0 WHERE discount_percent IS NULL;
