# Sheet spec — tab "Dishes" (the script creates it and writes row 1 automatically)

| column | example | meaning |
|---|---|---|
| timestamp | 2026-10-09T20:30:00.000Z | when it was added (UTC) |
| id | g1791600000000 | stable card id (`g` + milliseconds); used for #links |
| name | 葱油拌面 | dish name (required, ≤60 chars) |
| where | menu / todo | 菜单 or 📝 待做 |
| section | beef, pork, poultry, sea, cold, soup, staple, lunch, other, sweet | menu section (empty for 待做) |
| protein | 牛 猪 羊 鸡 鸭 鱼 龙虾/虾 蟹 蛤蜊/贝 豆腐/蛋 素 (or empty) | protein tag used by the picker's no-repeat rule |
| recent | yes / empty | 最近 tag |
| soup | yes / empty | counts as a soup (also automatic for the 汤 section or a name containing 汤) |
| link | https://… | recipe link (shown as a tag at the top of the sheet) |
| ingredients | 面 · 葱 · 酱油 | ingredient line |
| photo | https://lh3.googleusercontent.com/d/<id>=w1200 | photo URL (file lives in Drive folder "Family Menu photos") |
| photo_id | <Drive file id> | Drive file id (site falls back to drive.google.com/thumbnail?id=… if needed) |
| hide | anything | type anything here to hide a row from the site (no need to delete) |

Header row (row 1), tab-separated:
timestamp	id	name	where	section	protein	recent	soup	link	ingredients	photo	photo_id	hide
