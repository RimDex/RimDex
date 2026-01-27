---
title: Загрузка и установка
parent: Руководство пользователя
nav_order: 1
permalink: user-guide/downloading-and-installing
lang: ru
---

# Загрузка и установка

{: .warning }

> Большинству пользователей достаточно [готовых релизов](https://github.com/RimDex/RimDex/releases), а не ZIP исходников с GitHub.

Есть **Stable** и **Edge** сборки. Edge выходят чаще, но могут быть менее стабильны.

## Windows

- Скачайте архив `Windows x86-64`
- Запустите `RimDex.exe`
- При ложном срабатывании Defender добавьте исключение

## macOS

При ошибке «повреждён» выполните:

```bash
xattr -d com.apple.quarantine /path/to/RimDex.app
xattr -d com.apple.quarantine /path/to/libsteam_api.dylib
```

## Linux

- Скачайте `Linux x86-64`
- Сделайте исполняемым и запустите бинарник
- Для Qt WebEngine на некоторых дистрибутивах нужны системные библиотеки WebEngine

## Первый запуск

RimDex предложит указать пути к RimWorld, папке конфигурации и локальным модам, а также настроить SteamCMD при необходимости.
