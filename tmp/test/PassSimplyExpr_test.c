int main()
{
  int i = 0;
  int n = 0;
  int k = __VERIFIER_nondet_int();
  if (!((k <= 10000) && (k >= (-10000))))
  {
    return 0;
  }

  i = 0;
  while (i < (2 * k))
  {
    if ((i % 2) == 0)
    {
      n = n + 1;
    }

    i = i + 1;
  }

  __VERIFIER_assert((k < 0) || (n == k));
  return 0;
}

