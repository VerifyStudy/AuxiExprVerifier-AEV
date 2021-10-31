extern void __assert_fail(const char *, const char *, unsigned int, const char *) __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__noreturn__));
void reach_error() { __assert_fail("0", "linear-inequality-inv-a.c", 2, "reach_error"); }
extern unsigned char __VERIFIER_nondet_uchar(void);
void __VERIFIER_assert(int cond)
{
  if (!(cond))
  {
  ERROR:
  {
    reach_error();
    abort();
  }
  }
  return;
}
int main() {
  unsigned char n = __VERIFIER_nondet_uchar();
  if (n == 0) {
    return 0;
  }
  unsigned char v = 0;
  unsigned int  s = 0;
  unsigned int  i = 0;
  while (i < n) {
    v = __VERIFIER_nondet_uchar();
    s += v;
    ++i;
  }
  // if (s < v) {
  //   reach_error();
  //   return 1;
  // }
  // if (s > 65025) {
  //   reach_error();
  //   return 1;
  // }
  // should subtitute with __VERIFIER_assert(s < v || s > 65025);
  __VERIFIER_assert(s < v || s > 65025);
  return 0;
}
