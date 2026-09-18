# Roadmap UkrCode

- [x] Lexer з українськими іменами та відступами
- [x] Parser і AST для базового синтаксису
- [x] Інтерпретатор та CLI `ucod`
- [x] Базова стандартна бібліотека
- [x] Приклади та regression-тести
- [x] VS Code grammar і snippets
- [x] Telegram Bot API adapter з polling та обробниками
- [ ] Повна система типів та semantic diagnostics
- [ ] Bytecode VM та оптимізатор
- [ ] Package manager, `ucod.toml` і lock-файл
- [ ] Discord adapter
- [ ] Language Server Protocol і debugger
- [ ] Native compiler

## Що вже можна робити

Telegram MVP підтримує токен через environment variable, polling, команди,
отримання текстових повідомлень і відповіді в чат. Для невеликого бота цього
достатньо. Для production ще потрібні обмеження rate limit, middleware, FSM,
webhook, structured logging і повніші типи повідомлень.