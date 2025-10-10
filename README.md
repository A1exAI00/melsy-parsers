# melsy-parsers

## How to compile

### For windows

1. Open Cmd.
2. Change directory to Desktop.
```
cd Deskop
```

3. Copy project folder from Github to Desktop


- Compile `parser-LIV` for production (without stdout window):
```
pyinstaller melsy-parsers\parser-LIV\main.py -D -F -n "parser-LIV-v1.xx" -i icon.ico -w
```
- Compile `parser-LIV` for debug (with stdout window):
```
pyinstaller melsy-parsers\parser-LIV\main.py -D -F -n "parser-LIV-v1.xx" -i icon.ico
```
- Compile `parser-LT` for production (without stdout window):
```
pyinstaller melsy-parsers\parser-LT-GIVIK\main.py -D -F -n "parser-LT-v1.xx" -i icon.ico -w
```
- Compile `parser-LT` for debug (with stdout window):
```
pyinstaller melsy-parsers\parser-LT-GIVIK\main.py -D -F -n "parser-LT-v1.xx" -i icon.ico
```

4. Open `.\dist` directory, there is your `.exe` file
5. Enjoy!
