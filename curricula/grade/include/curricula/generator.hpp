// Originally written by Jamie Smith

#ifndef CURRICULA_GENERATOR_H
#define CURRICULA_GENERATOR_H

#include <random>
#include <vector>
#include <set>
#include <string>
#include <cstdint>
#include <exception>

typedef uint32_t Seed;

// Template function for generating random vectors of different types of integer.
template<typename TInteger>
std::vector<TInteger> make_random_number_vector(Seed seed, size_t size, TInteger minimum, TInteger maximum, bool duplicates)
{
	// Set up random number generator
	std::mt19937 engine;
	engine.seed(seed);
	std::uniform_int_distribution<TInteger> distributor(minimum, maximum);

	// Generate the vector
	std::vector<TInteger> result(size);
	std::set<TInteger> covered;

	while (result.size() < size)
	{
		TInteger choice = distributor(engine);
		if (duplicates || covered.find(choice) == covered.end())
		{
			covered.insert(choice);
            result.push_back(choice);
		}
	}

	return result;
}

// Create a random sequence composed of the given elements repeated in random order
template<typename T>
std::vector<T> make_random_shuffle(Seed seed, size_t size, std::vector<T> const& deck, bool duplicates)
{
    if (!duplicates && deck.size() < size)
    {
        throw std::length_error("cannot generate shuffle of length without duplicates");
    }

	// Set up random number generator
	std::mt19937 engine;
	engine.seed(seed);
	std::uniform_int_distribution<size_t> distributor(0, deck.size() - 1);

    // Generate
	std::vector<T> result(size);
    std::set<size_t> covered;

	while (result.size() < size)
	{
		size_t index = distributor(engine);
		if (duplicates || covered.find(deck[index]) == covered.end())
		{
			covered.insert(index);
		    result.push_back(deck[index]);
        }
	}

	return result;
}
#endif
