# Revit View Exporter

Плагин для Revit, который позволяет извлекать виды из Revit файлов в виде изображений.

## Возможности

- Отображение списка всех видов в текущем документе Revit
- Фильтрация видов по имени и типу
- Экспорт выбранных видов в формате PNG
- Высокое качество экспорта (300 DPI)

## Требования

- Autodesk Revit 2022 или новее
- .NET Framework 4.8
- Visual Studio 2019 или новее (для сборки)

## Установка

### Автоматическая установка

1. Скачайте последнюю версию плагина из раздела [Releases](https://github.com/yourusername/RevitViewExporter/releases)
2. Запустите установщик и следуйте инструкциям

### Ручная установка

1. Скомпилируйте проект в Visual Studio
2. Скопируйте файлы `RevitViewExporter.dll` и `RevitViewExporter.addin` в папку:
   - `C:\Users\[UserName]\AppData\Roaming\Autodesk\Revit\Addins\[RevitVersion]\`

## Использование

1. Запустите Revit и откройте файл
2. На вкладке "View Exporter" нажмите кнопку "Export Views"
3. В появившемся окне:
   - Используйте фильтр для поиска нужных видов
   - Выберите виды для экспорта
   - Нажмите кнопку "Export"
4. Выберите папку для сохранения изображений
5. Дождитесь завершения экспорта

## Настройка

Вы можете изменить параметры экспорта, отредактировав код в файле `ExportViewsCommand.cs`:

```csharp
// Настройки экспорта
options.ZoomType = ZoomFitType.FitToPage;
options.PixelSize = 2000; // Ширина изображения в пикселях
options.ImageResolution = ImageResolution.DPI_300; // Разрешение
options.HLRandWFViewsFileType = ImageFileType.PNG; // Формат файла
```

## Сборка из исходного кода

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/yourusername/RevitViewExporter.git
   ```

2. Откройте проект в Visual Studio:
   ```
   RevitViewExporter.sln
   ```

3. Обновите пути к Revit API DLL в ссылках проекта, если необходимо:
   - RevitAPI.dll
   - RevitAPIUI.dll

4. Скомпилируйте проект (Build > Build Solution)

## Лицензия

MIT License

