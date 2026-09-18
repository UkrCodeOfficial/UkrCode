const vscode = require('vscode');

const keywords = [
  'якщо', 'інакше', 'для', 'у', 'поки', 'повторити', 'разів', 'функція',
  'повернути', 'клас', 'імпортувати', 'як', 'асинхронна', 'чекати',
  'спробувати', 'помилка', 'нарешті', 'підняти', 'перервати', 'продовжити',
  'коли', 'так', 'ні', 'нічого'
];

const modules = ['Математика', 'Текст', 'Списки', 'JSON', 'Файли', 'ОС', 'Дата', 'Час', 'Випадковість', 'РегулярніВирази', 'Термінал', 'Процеси', 'Логування', 'HTTP', 'БазаДаних', 'Telegram', 'Discord'];
const botMethods = ['команда', 'отримав_повідомлення', 'отримав_текст', 'натиснули_кнопку', 'відповісти', 'надіслати_фото', 'надіслати_документ', 'редагувати_повідомлення', 'видалити_повідомлення', 'сесія', 'є_адмін', 'створити_замовлення', 'отримати_замовлення', 'запустити'];
const builtins = ['написати', 'введення', 'діапазон', 'довжина', 'тип', 'текст', 'ціле', 'дробове', 'сума', 'мінімум', 'максимум', 'перелічити', 'відсортувати', 'набір'];

function completionItem(label, kind, detail, insertText) {
  const item = new vscode.CompletionItem(label, kind);
  item.detail = detail;
  item.insertText = insertText || label;
  return item;
}

function run(command, file) {
  const terminal = vscode.window.createTerminal('UkrCode');
  terminal.show();
  terminal.sendText(`${command} "${file}"`);
}

function activate(context) {
  const file = () => vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.fileName;
  context.subscriptions.push(vscode.commands.registerCommand('ukrcode.runFile', () => run('ucod run', file())));
  context.subscriptions.push(vscode.commands.registerCommand('ukrcode.checkFile', () => run('ucod check', file())));
  context.subscriptions.push(vscode.commands.registerCommand('ukrcode.formatFile', () => run('ucod format', file())));

  context.subscriptions.push(vscode.languages.registerCompletionItemProvider('ukrcode', {
    provideCompletionItems(document, position) {
      const line = document.lineAt(position.line).text.slice(0, position.character);
      const items = [];
      if (/бот\.$|повідомлення\.$/.test(line)) {
        botMethods.forEach(method => items.push(completionItem(method, vscode.CompletionItemKind.Method, 'UkrCode Telegram API')));
      } else {
        keywords.forEach(keyword => items.push(completionItem(keyword, vscode.CompletionItemKind.Keyword, 'Ключове слово UkrCode')));
        modules.forEach(module => items.push(completionItem(module, vscode.CompletionItemKind.Module, 'Стандартний модуль UkrCode')));
        builtins.forEach(name => items.push(completionItem(name, vscode.CompletionItemKind.Function, 'Вбудована функція UkrCode')));
        items.push(completionItem('telegrambot', vscode.CompletionItemKind.Snippet, 'Шаблон Telegram-бота', new vscode.SnippetString('імпортувати Telegram\n\nбот = Telegram.Бот(середовище("BOT_TOKEN"))\n\nколи бот.команда("/start"):\n    бот.відповісти("Привіт!")\n\nбот.запустити()')));
        items.push(completionItem('клас', vscode.CompletionItemKind.Snippet, 'Шаблон класу', new vscode.SnippetString('клас ${1:Назва}:\n    функція ініціалізувати(цей):\n        ${0}')));
      }
      return items;
    }
  }, ' ', '.', '_'));

  context.subscriptions.push(vscode.languages.registerHoverProvider('ukrcode', {
    provideHover(document, position) {
      const word = document.getText(document.getWordRangeAtPosition(position));
      const docs = {
        'бот': '**бот**\n\nЕкземпляр Telegram.Бот у UkrCode.',
        'відповісти': '**бот.відповісти(текст, кнопки, inline_кнопки)**\n\nНадсилає повідомлення у поточний чат.',
        'натиснули_кнопку': '**бот.натиснули_кнопку(дані)**\n\nОбробник Telegram callback query.',
        'сесія': '**бот.сесія(ідентифікатор)**\n\nПовертає сесію користувача для стану кошика або діалогу.',
        'створити_замовлення': '**бот.створити_замовлення(користувач, послуга, ціна)**\n\nСтворює замовлення у памʼяті runtime.'
      };
      return docs[word] ? new vscode.Hover(new vscode.MarkdownString(docs[word])) : undefined;
    }
  }));
}

exports.activate = activate;
exports.deactivate = function () {};