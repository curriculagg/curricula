#include <vector>

template<typename T, typename Comparator>
int is_sorted(std::vector<T> const& list, size_t size, Comparator& comparator)
{
	if (size != list.size())
	{
		return 1;
	}

	for (size_t i = 1; i < size; ++i)
	{
		if (comparator(list[i], list[i - 1]))
		{
			return 1;
		}
	}

	return 0;
}
