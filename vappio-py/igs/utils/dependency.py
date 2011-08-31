#
# My attempt at Smalltalk-like dependency setup


class DependentFor:
    def __init__(self, dependents=[]):
        self.dependents = []
        self.dependents.extend(dependents)

    def change(self, aspect=None, value=None):
        for d in self.dependents:
            d.update(self, aspect, value)
