import math

from dataclasses import dataclass
from typing import Sequence, Callable, Iterable


@dataclass()
class RuntimeDataPoint:
    n: float
    count: float


class RuntimeDataTransform:
    """Transforms for 2D data."""

    @classmethod
    def n_log_n(cls, point: RuntimeDataPoint) -> RuntimeDataPoint:
        return RuntimeDataPoint(math.log(point.n), point.count)


@dataclass(eq=False)
class RuntimeData:
    points: Sequence[RuntimeDataPoint]

    @classmethod
    def build(cls, raw: Iterable[Iterable[float]]) -> "RuntimeData":
        return RuntimeData(tuple(RuntimeDataPoint(*point) for point in sorted(raw, key=lambda p: p[0])))

    def transform(self, profile: Callable[[RuntimeDataPoint], RuntimeDataPoint]) -> "RuntimeData":
        return RuntimeData(tuple(map(profile, self.points)))

    def linearity(self) -> float:
        """Calculate linear regression error.

        This method computes the linear regression of the data,
        uses the slope and intercept to determine error, then returns
        a factor describing how close to linear the data set is.

        This was developed by Jamie Smith. From his notes:

        > In my preliminary testing, I found that comparing the
        > average error and average y^2 values was a reasonable test
        > for how linear the data is. If the average y^2 is an order
        > of magnitude or two greater than the average error, the data
        > is more or less linear. This ratio also has the nice
        > property that if you multiply all times by a scalar, it
        > stays the same, so if the user's function gets 10x faster in
        > every case, the correlation factor doesn't change at all.
        """

        sum_xy = sum_x = sum_y = sum_x_squared = sum_y_squared = 0
        for point in self.points:
            sum_xy += point.n * point.count
            sum_x += point.n
            sum_y += point.count
            sum_x_squared += point.n * point.n
            sum_y_squared += point.count * point.count

        m = (len(self.points) * sum_xy - sum_x * sum_y) / (len(self.points) * sum_x_squared - sum_x * sum_x)
        b = (sum_y - m * sum_x) / len(self.points)

        sum_error_squared = 0
        for point in self.points:
            expected = m * point.n + b
            sum_error_squared += (expected - point.count) ** 2

        average_error_squared = sum_error_squared / len(self.points)
        average_y_squared = sum_y_squared / len(self.points)
        if average_error_squared == 0:
            return float("inf")
        return math.log10(average_y_squared) - math.log10(average_error_squared)
