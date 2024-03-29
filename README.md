# Almond 

Almond - это фреймворк для динамической подстановки аргументов в объекты.

## Пример

```python
from almond.almond import X, XContext, XSupport, XStaticProducer, xbuild

class WhatIsUp(XSupport):

    want_this: X[int]
    and_this: X[bool]

    def is_up(self):
        print(f"want_this: {self.want_this}")
        print(f"and_this: {self.and_this}")


def main():
    context: XContext = {
        int: XStaticProducer(12),
        bool: XStaticProducer(False),
    }
    WhatIsUp.compile(context)

    with xbuild(WhatIsUp) as what:
        what.is_up()


if __name__ == "__main__":
    main()
```

Запустив этот код, вы увидите следующий вывод:

```
want_this: 12
and_this: False
```
