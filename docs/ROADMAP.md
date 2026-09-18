# Roadmap UkrCode

- [x] Lexer з українськими іменами та відступами
- [x] Parser і AST для базового синтаксису
- [x] Класи, обʼєкти, конструктори, методи та просте наслідування
- [x] Інтерпретатор та CLI `ucod`
- [x] Базова стандартна бібліотека
- [x] Приклади та regression-тести
- [x] VS Code grammar і snippets
- [x] Telegram Bot API adapter з polling та обробниками
- [x] Telegram keyboards, callback queries, media та message operations
- [ ] Повна система типів та semantic diagnostics
- [ ] Bytecode VM та оптимізатор
- [x] Локальний package manager, `ucod.toml` і `ucod.lock`
- [x] Discord webhook adapter для outbound-повідомлень
- [ ] Повний Discord Gateway/slash commands adapter
- [ ] Language Server Protocol і debugger
- [ ] Native compiler

## Що вже можна робити

Telegram MVP підтримує токен через environment variable, polling, команди,
отримання текстових повідомлень і відповіді в чат. Для невеликого бота цього
достатньо. Для production ще потрібні обмеження rate limit, middleware, FSM,
webhook, structured logging і повніші типи повідомлень.