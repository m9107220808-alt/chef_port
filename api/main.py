from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.config import settings
from api.routes import products, orders, users

# Создаём приложение FastAPI
app = FastAPI(
    title="ChefPort API",
    description="API для бота ChefPort - морепродукты с доставкой",
    version="1.0.0",
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


@app.get("/", response_class=HTMLResponse)
async def root_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Каталог Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg-main: #020617;
      --bg-main2: #041526;
      --accent: #38bdf8;
      --accent-strong: #0ea5e9;
      --text-main: #f9fafb;
      --text-soft: #cbd5f5;
      --card-bg: #020617;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, system-ui, sans-serif;
      background: radial-gradient(circle at top, #082f49 0, #020617 60%, #000 100%);
      min-height: 100vh;
      color: var(--text-main);
      padding: 12px;
    }
    .app {
      max-width: 430px;
      margin: 0 auto;
      position: relative;
      overflow: hidden;
    }

    /* Абстрактные \"тарелки\" по краям (без текста и роллов) */
    .plate {
      position: absolute;
      width: 96px;
      height: 96px;
      border-radius: 999px;
      background: radial-gradient(circle at 30% 30%, #f97316 0, #fb923c 35%, #0f172a 100%);
      opacity: 0.9;
      box-shadow: 0 12px 30px rgba(15,23,42,0.7);
      border: 6px solid #f9fafb;
      overflow: hidden;
    }
    .plate::after {
      content: "";
      position: absolute;
      inset: 18%;
      border-radius: 999px;
      background: radial-gradient(circle at 40% 20%, #fecaca 0, #fee2e2 40%, #991b1b 90%);
      opacity: 0.9;
      filter: saturate(1.1);
    }
    .plate--tl { top: -28px; left: -30px; transform: rotate(-10deg); }
    .plate--tr { top: -40px; right: -40px; transform: rotate(15deg); }
    .plate--bl { bottom: -40px; left: -40px; transform: rotate(12deg); }
    .plate--br { bottom: -48px; right: -32px; transform: rotate(-18deg); }

    /* Верхний блок */
    .hero {
      position: relative;
      z-index: 1;
      padding: 18px 16px 14px;
      border-radius: 22px;
      background: linear-gradient(135deg, #020617 0, #0f172a 40%, #0369a1 100%);
      box-shadow: 0 18px 40px rgba(15,23,42,0.9);
      margin-bottom: 18px;
    }
    .hero-title {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }
    .hero-sub {
      font-size: 13px;
      color: var(--text-soft);
      line-height: 1.4;
      max-width: 90%;
    }

    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
      font-size: 11px;
    }
    .badge {
      padding: 4px 9px;
      border-radius: 999px;
      background: rgba(15,23,42,0.7);
      border: 1px solid rgba(148,163,184,0.7);
      color: #e5e7eb;
    }
    .badge--accent {
      background: rgba(56,189,248,0.15);
      border-color: rgba(56,189,248,0.8);
      color: #e0f2fe;
    }

    /* Центральный оффер */
    .offer {
      margin-top: 14px;
      padding: 10px 12px;
      border-radius: 16px;
      background: linear-gradient(90deg, var(--accent-strong), var(--accent));
      color: #0b1120;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    .offer-main {
      font-size: 14px;
      font-weight: 700;
    }
    .offer-sub {
      font-size: 11px;
      opacity: 0.9;
    }
    .offer-step {
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(15,23,42,0.1);
      font-weight: 600;
    }

    /* Категории */
    .section-title {
      margin-top: 18px;
      margin-bottom: 6px;
      font-size: 15px;
      font-weight: 600;
    }
    .section-sub {
      font-size: 11px;
      color: #9ca3af;
      margin-bottom: 8px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .card {
      background: rgba(15,23,42,0.92);
      border-radius: 15px;
      padding: 10px 11px;
      box-shadow: 0 12px 24px rgba(15,23,42,0.9);
      border: 1px solid rgba(148,163,184,0.35);
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
    }
    .card-icon {
      font-size: 16px;
    }
    .card-body {
      font-size: 12px;
      color: #9ca3af;
      line-height: 1.35;
    }

    /* Хиты */
    .hits-row {
      margin-top: 10px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .hit-card {
      min-width: 160px;
      background: rgba(15,23,42,0.95);
      border-radius: 14px;
      padding: 8px 9px;
      border: 1px solid rgba(56,189,248,0.4);
    }
    .hit-name {
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 2px;
    }
    .hit-meta {
      font-size: 11px;
      color: #9ca3af;
    }
    .hit-footer {
      margin-top: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
    }
    .hit-price {
      color: #facc15;
      font-weight: 700;
    }
    .hit-abc {
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(21,128,61,0.2);
      color: #bbf7d0;
    }

    /* Низ */
    .cta {
      margin-top: 14px;
      padding: 10px 11px;
      border-radius: 14px;
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(148,163,184,0.5);
      font-size: 11px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    .cta button {
      border: none;
      border-radius: 999px;
      padding: 6px 13px;
      font-size: 12px;
      font-weight: 600;
      background: #22c55e;
      color: #022c22;
    }
  </style>
</head>
<body>
<div class="app">
  <div class="plate plate--tl"></div>
  <div class="plate plate--tr"></div>
  <div class="plate plate--bl"></div>
  <div class="plate plate--br"></div>

  <div class="hero">
    <div class="hero-title">Каталог Mini Apps</div>
    <p class="hero-sub">
      Рыба, морепродукты, стейки и готовые блюда. Оформите заказ прямо в Telegram.
    </p>
    <div class="hero-badges">
      <span class="badge badge--accent">Топ A‑товары по продажам</span>
      <span class="badge">Доставка из ближайшего магазина</span>
      <span class="badge">Прозрачные веса и цены</span>
    </div>

    <div class="offer">
      <div>
        <div class="offer-main">Оформите заказ за 3 шага</div>
        <div class="offer-sub">Категория → товар → подтверждение</div>
      </div>
      <div class="offer-step">Начните с каталога</div>
    </div>
  </div>

  <div class="section-title">Категории</div>
  <div class="section-sub">Выберите раздел, остальное Mini App сделает за вас.</div>

  <div class="grid">
    <div class="card">
      <div class="card-header">
        <div class="card-title">🐟 Рыба</div>
        <div class="card-icon">➜</div>
      </div>
      <div class="card-body">Стейки и тушки для запекания, жарки и гриля.</div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">🦐 Морепродукты</div>
        <div class="card-icon">➜</div>
      </div>
      <div class="card-body">Креветки, мидии, кальмар и другие деликатесы.</div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">🔥 Гриль / стейки</div>
        <div class="card-icon">➜</div>
      </div>
      <div class="card-body">Готовые к жарке стейки и маринованная рыба.</div>
    </div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">🍽 Готовые блюда</div>
        <div class="card-icon">➜</div>
      </div>
      <div class="card-body">Блюда, которые достаточно разогреть.</div>
    </div>
  </div>

  <div class="section-title">Хиты продаж (A‑группа)</div>
  <div class="section-sub">Товары, которые дают основную выручку по ABC‑анализу.</div>

  <div class="hits-row">
    <div class="hit-card">
      <div class="hit-name">Стейк лосося</div>
      <div class="hit-meta">Средний вес 0.3–0.5 кг</div>
      <div class="hit-footer">
        <span class="hit-price">≈ 1 200 ₽ / уп.</span>
        <span class="hit-abc">A‑группа</span>
      </div>
    </div>
    <div class="hit-card">
      <div class="hit-name">Дорадо в маринаде</div>
      <div class="hit-meta">Прованский / средиземноморский</div>
      <div class="hit-footer">
        <span class="hit-price">≈ 750 ₽ / шт.</span>
        <span class="hit-abc">A‑категория</span>
      </div>
    </div>
  </div>

  <div class="cta">
    <div>
      Откройте каталог через кнопку в боте, чтобы увидеть все товары с приоритетом A‑группы и актуальными ценами.
    </div>
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
