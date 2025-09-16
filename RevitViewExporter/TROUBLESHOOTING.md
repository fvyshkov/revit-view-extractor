# Устранение проблем при сборке RevitViewExporter

## Ошибки типа "The type or namespace name 'Autodesk' could not be found"

Эта ошибка возникает, когда Visual Studio не может найти библиотеки Revit API. Вот как это исправить:

### Решение 1: Добавьте ссылки на Revit API вручную

1. **Откройте проект в Visual Studio**
2. **Щелкните правой кнопкой мыши на проекте** в Solution Explorer
3. **Выберите "Add" > "Reference..."**
4. **Нажмите "Browse"** и найдите следующие DLL-файлы:
   - `RevitAPI.dll`
   - `RevitAPIUI.dll`

Эти файлы обычно находятся в папке установки Revit:
```
C:\Program Files\Autodesk\Revit 2022\RevitAPI.dll
C:\Program Files\Autodesk\Revit 2022\RevitAPIUI.dll
```

### Решение 2: Используйте NuGet-пакеты

1. **Щелкните правой кнопкой мыши на проекте**
2. **Выберите "Manage NuGet Packages..."**
3. **Найдите и установите пакеты**:
   - `Revit.RevitAPI.x64`
   - `Revit.RevitAPIUI.x64`

### Решение 3: Отредактируйте файл проекта

1. **Откройте файл RevitViewExporter.csproj** в текстовом редакторе
2. **Найдите раздел с ссылками** (References)
3. **Обновите пути к DLL-файлам**, чтобы они соответствовали вашей установке Revit:

```xml
<Reference Include="RevitAPI">
  <HintPath>C:\Program Files\Autodesk\Revit XXXX\RevitAPI.dll</HintPath>
  <Private>False</Private>
</Reference>
<Reference Include="RevitAPIUI">
  <HintPath>C:\Program Files\Autodesk\Revit XXXX\RevitAPIUI.dll</HintPath>
  <Private>False</Private>
</Reference>
```

Замените `XXXX` на вашу версию Revit (например, 2022, 2023, и т.д.).

## Ошибки при сборке проекта

### Неправильная версия .NET Framework

Убедитесь, что используется .NET Framework 4.8:

1. **Щелкните правой кнопкой мыши на проекте**
2. **Выберите "Properties"**
3. **Перейдите на вкладку "Application"**
4. **Убедитесь, что "Target framework" установлен на ".NET Framework 4.8"**

### Конфликты версий Revit API

Если вы используете версию Revit API, которая не соответствует вашей версии Revit:

1. **Удалите существующие ссылки** на RevitAPI.dll и RevitAPIUI.dll
2. **Добавьте правильные ссылки** для вашей версии Revit

### Ошибки с ProgressBar

Если вы получаете ошибки, связанные с классом ProgressBar:

1. **Откройте файл ExportViewsCommand.cs**
2. **Замените код ProgressBar** на следующий:

```csharp
// Создаем простую форму прогресса
Form progressForm = new Form();
progressForm.Text = "Exporting Views...";
progressForm.Size = new System.Drawing.Size(400, 100);
progressForm.StartPosition = FormStartPosition.CenterScreen;
progressForm.FormBorderStyle = FormBorderStyle.FixedDialog;
progressForm.MaximizeBox = false;
progressForm.MinimizeBox = false;

ProgressBar progressBar = new ProgressBar();
progressBar.Minimum = 0;
progressBar.Maximum = views.Count;
progressBar.Value = 0;
progressBar.Width = 360;
progressBar.Location = new System.Drawing.Point(20, 20);

Label progressLabel = new Label();
progressLabel.Text = "Preparing...";
progressLabel.Location = new System.Drawing.Point(20, 50);
progressLabel.Width = 360;

progressForm.Controls.Add(progressBar);
progressForm.Controls.Add(progressLabel);
progressForm.Show();

// Далее в цикле:
progressBar.Value = exportedCount + 1;
progressLabel.Text = $"Exporting {exportedCount + 1} of {views.Count}: {view.Name}";
Application.DoEvents();

// После завершения:
progressForm.Close();
```

## Проблемы при установке плагина

### Плагин не появляется в Revit

1. **Проверьте, что файлы скопированы в правильную папку**:
   ```
   C:\Users\[UserName]\AppData\Roaming\Autodesk\Revit\Addins\[RevitVersion]\
   ```

2. **Проверьте журнал Revit** на наличие ошибок загрузки плагина:
   - Запустите Revit
   - Выберите меню: File > Options
   - Перейдите на вкладку "Journal and notification configuration"
   - Найдите расположение журналов
   - Проверьте последний журнал на наличие ошибок, связанных с вашим плагином

3. **Убедитесь, что плагин собран для правильной версии Revit**

