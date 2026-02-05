# Скрипт для копирования сгенерированных изображений в проект
$sourceDir = "C:\Users\Евгений\.gemini\antigravity\brain\0d68a766-6efe-43e7-8b69-934437e97d01"
$targetDir = "z:\chefport-bot\web\images"

# Создаём папку если не существует
New-Item -ItemType Directory -Force -Path $targetDir

# Копируем изображения с понятными именами
# Красивые фото категорий
Copy-Item "$sourceDir\category_fish_1770240380968.png" "$targetDir\category_fish.png" -Force
Copy-Item "$sourceDir\category_caviar_1770240409545.png" "$targetDir\category_caviar.png" -Force
Copy-Item "$sourceDir\category_seafood_1770240395581.png" "$targetDir\category_seafood.png" -Force
Copy-Item "$sourceDir\seafood_category_hero_1770240350047.png" "$targetDir\hero.png" -Force

# Дополнительные варианты
Copy-Item "$sourceDir\category_fish_1770240439250.png" "$targetDir\fish_salmon.png" -Force
Copy-Item "$sourceDir\category_seafood_1770240453412.png" "$targetDir\seafood_mix.png" -Force

# Баннер с акцией
Copy-Item "$sourceDir\media__1770237626167.jpg" "$targetDir\promo_banner.jpg" -Force

Write-Host "✅ Изображения скопированы в $targetDir"
Write-Host ""
Write-Host "📁 Список файлов:"
Get-ChildItem $targetDir | Format-Table Name, Length -AutoSize
