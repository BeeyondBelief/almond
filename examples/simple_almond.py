from almond.builder import xbuild
from almond.producer import StaticAlmondProducer
from almond.resolver import AlmondContext
from almond.support import Almond, AlmondSupport


class WhatIsUp(AlmondSupport):
    want_this: Almond[int]
    and_this: Almond[bool]

    def is_up(self):
        print(f"want_this: {self.want_this}")
        print(f"and_this: {self.and_this}")


def main():
    context: AlmondContext = {
        int: StaticAlmondProducer(12),
        bool: StaticAlmondProducer(False),
    }
    WhatIsUp.compile(context)

    with xbuild(WhatIsUp) as what:
        what.is_up()


if __name__ == "__main__":
    main()