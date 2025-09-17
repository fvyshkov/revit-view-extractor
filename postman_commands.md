# Postman/curl команды для тестирования APS Design Automation

## 1. Получить токен

```bash
curl -X POST "https://developer.api.autodesk.com/authentication/v2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n" \
  -d "client_secret=YOUR_SECRET_HERE" \
  -d "grant_type=client_credentials" \
  -d "scope=code:all"
```

## 2. Список наших Activities

```bash
curl -X GET "https://developer.api.autodesk.com/da/us-east/v3/activities" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 3. Создать простую Activity (без сложных параметров)

```bash
curl -X POST "https://developer.api.autodesk.com/da/us-east/v3/activities" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "SimpleTest",
    "commandLine": ["echo hello > result.txt"],
    "parameters": {
      "result": {
        "verb": "put",
        "description": "Output result file",
        "localName": "result.txt"
      }
    },
    "engine": "Autodesk.Revit+2026",
    "description": "Simple test activity"
  }'
```

## 4. Создать workitem с простой Activity

```bash
curl -X POST "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.SimpleTest",
    "arguments": {
      "result": {
        "url": "https://httpbin.org/put"
      }
    }
  }'
```

## 5. Тестировать системные Activities

```bash
# Autodesk.Nop (без параметров)
curl -X POST "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "Autodesk.Nop+Latest"
  }'
```

## 6. Получить информацию о конкретной Activity

```bash
curl -X GET "https://developer.api.autodesk.com/da/us-east/v3/activities/rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.ExtractViewsActivity" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 7. Проверить статус workitem

```bash
curl -X GET "https://developer.api.autodesk.com/da/us-east/v3/workitems/YOUR_WORKITEM_ID" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Postman Collection

Импортируй в Postman:
- URL: `https://raw.githubusercontent.com/autodesk-platform-services/aps-tutorials-postman/master/collections/DA4R%20-%20Tutorial.postman_collection.json`
- Environment: `https://raw.githubusercontent.com/autodesk-platform-services/aps-tutorials-postman/master/environments/DA4R%20-%20Tutorial.postman_environment.json`

Затем:
1. Установи переменные `client_id` и `client_secret`
2. Запусти "Get Access Token"
3. Тестируй workitems с разными activityId





