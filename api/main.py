from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse  # <-- Добавили этот импорт
from api.config import settings
from api.routes import products, orders, users

# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(products.router, prefix="/api/products", tags=["Товары"])
app.include_router(orders.router, prefix="/api/orders", tags=["Заказы"])
app.include_router(users.router, prefix="/api/users", tags=["Пользователи"])

# ЗАМЕНИЛИ старый @app.get("/") на этот:

@app.get("/", response_class=HTMLResponse)
async def root_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Шеф Порт — Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg-main: #041526;
      --bg-card: #ffffff;
      --accent: #00a0e3;
      --accent-soft: #e5f7ff;
      --text-main: #0f172a;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, system-ui, sans-serif;
      background: radial-gradient(circle at top, #082f49 0, #020617 55%, #000 100%);
      color: var(--text-main);
      padding: 12px;
    }
    .app {
      max-width: 420px;
      margin: 0 auto;
    }
    .hero {
      background: linear-gradient(135deg, #022c43, #035a84);
      border-radius: 20px;
      padding: 16px 16px 14px;
      color: #f9fafb;
      position: relative;
      overflow: hidden;
    }
    .hero::before {
      content: "🐟 🐠 🐡";
      position: absolute;
      right: 10px;
      top: 8px;
      opacity: 0.35;
      font-size: 22px;
    }
    .hero-title {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .hero-badge {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.2);
      border: 1px solid rgba(45, 212, 191, 0.6);
      color: #a7f3d0;
    }
    .hero-text {
      font-size: 13px;
      opacity: 0.9;
      margin-top: 4px;
    }
    .hero-meta {
      display: flex;
      gap: 8px;
      margin-top: 10px;
      font-size: 11px;
      opacity: 0.9;
    }
    .hero-meta span {
      padding: 3px 7px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.3);
    }

    .section-title {
      margin-top: 14px;
      margin-bottom: 6px;
      font-size: 15px;
      font-weight: 600;
      color: #e5e7eb;
    }
    .section-sub {
      font-size: 11px;
      color: #9ca3af;
      margin-bottom: 8px;
    }

    .chips {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .chip {
      font-size: 11px;
      white-space: nowrap;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.7);
      background: rgba(15, 23, 42, 0.7);
      color: #e5e7eb;
    }
    .chip.chip-hot {
      border-color: #f97316;
      background: rgba(248, 113, 113, 0.1);
      color: #fed7aa;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 6px;
    }
    .card {
      background: var(--bg-card);
      border-radius: 14px;
      padding: 10px 11px;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }
    .card-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-main);
    }
    .card-tag {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
    }
    .card-body {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 6px;
    }
    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
    }
    .price {
      font-weight: 700;
      color: var(--accent);
    }
    .abc-pill {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 999px;
      background: #022c22;
      color: #bbf7d0;
    }

    .cta {
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 14px;
      background: #022c22;
      color: #a7f3d0;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .cta button {
      border: none;
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 600;
      background: #22c55e;
      color: #022c22;
    }
  </style>
</head>
<body>
<div class="app">
  <div class="hero">
    <div class="hero-title">
      <span>🐟 Шеф Порт</span>
      <span class="hero-badge">Лучшее из моря — домой за 60 минут</span>
    </div>
    <p class="hero-text">
      Свежая рыба, стейки и морепродукты из вашего магазина Шеф Порт. 
      Оформите заказ прямо в Mini App.
    </p>
    <div class="hero-meta">
      <span>Топ A‑товары по продажам</span>
      <span>Доставка по Смоленску</span>
    </div>
  </div>

  <div class="section-title">🔥 Хиты продаж</div>
  <div class="section-sub">Группа A из ABC‑анализа — первые в выдаче каталога</div>

  <div class="chips">
    <div class="chip chip-hot">Стейк лосося ЧИЛИ</div>
    <div class="chip">Стейк форели</div>
    <div class="chip">Кальмар с гребешком</div>
    <div class="chip">Дорадо маринад</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-header">
        <div class="card-title">Стейк лосося ЧИЛИ</div>
        <span class="card-tag">A‑группа</span>
      </div>
      <div class="card-body">
        Лидер по выручке, идеален для гриля. 
        Средний вес порции — 0.3–0.5 кг.
      </div>
      <div class="card-footer">
        <span class="price">≈ 1 200 ₽ / уп.</span>
        <span class="abc-pill">4.15% выручки</span>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div class="card-title">Дорадо в маринаде</div>
        <span class="card-tag">Гриль / духовка</span>
      </div>
      <div class="card-body">
        Прованский или средиземноморский маринад, 
        рыба готова к запеканию.
      </div>
      <div class="card-footer">
        <span class="price">≈ 750 ₽ / шт.</span>
        <span class="abc-pill">Топ A‑категория</span>
      </div>
    </div>
  </div>

  <div class="section-title">Категории</div>
  <div class="section-sub">Нажмите «Открыть каталог» в боте, чтобы перейти к полному списку</div>

  <div class="grid">
    <div class="card">
      <div class="card-header">
        <div class="card-title">🐟 Рыба</div>
      </div>
      <div class="card-body">Форель, семга, дорадо, сибас — стейки и тушка.</div>
      <div class="card-footer">
        <span>По ABC выше — сначала хиты</span>
      </div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">🦐 Морепродукты</div>
      </div>
      <div class="card-body">Креветки, мидии, кальмары, гребешок и другие деликатесы.</div>
      <div class="card-footer">
        <span>Для паст, салатов и гриля</span>
      </div>
    </div>
  </div>

  <div class="cta">
    <div>Откройте каталог через кнопку в Telegram, чтобы увидеть весь ассортимент по категориям и ABC‑приоритету.</div>
    <button onclick="Telegram?.WebApp?.close()">Закрыть</button>
  </div>
</div>

<script>
  if (window.Telegram?.WebApp) {
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();
    console.log('Telegram WebApp init:', Telegram.WebApp.initDataUnsafe);
  }
</script>
</body>
</html>
"""



@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Блок запуска (оставляем без изменений)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
