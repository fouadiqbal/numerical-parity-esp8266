#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>

using std::size_t;

template <typename T>
constexpr T constrain(T value, T lower, T upper) {
  return value < lower ? lower : (value > upper ? upper : value);
}
