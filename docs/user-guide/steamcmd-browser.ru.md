---
title: SteamCMD и браузер мастерской
nav_order: 5
parent: Руководство пользователя
permalink: user-guide/steamcmd-browser
lang: ru
---

# SteamCMD и браузер мастерской

[SteamCMD][SteamCMD] — утилита Valve для загрузки модов мастерской без клиента Steam. RimDex встраивает браузер мастерской и загрузчик через SteamCMD или Steam.

## Настройка SteamCMD

**Settings → SteamCMD** — путь установки и параметры. При первом использовании RimDex может предложить автоматическую установку.

## Браузер мастерской

**File → Steam Workshop Browser** (или аналог в меню) открывает встроенный браузер:

- Добавление модов в список загрузки с карточек (**Add to list**)
- Загрузка через SteamCMD или подписка через Steam-клиент

## Обновление модов SteamCMD

RimDex может проверять обновления модов, установленных через SteamCMD.

## Логи SteamCMD

Логи — в `{steamcmd_install}/logs/`. Вывод также попадает в `RimDex.log` на уровне INFO.

## Устранение неполадок

- Очистите depot cache и `.acf` через **Settings → SteamCMD**
- Проверьте сеть и firewall

[SteamCMD]: https://developer.valvesoftware.com/wiki/SteamCMD
