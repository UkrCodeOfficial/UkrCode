const vscode = require('vscode');

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
}

exports.activate = activate;
exports.deactivate = function () {};