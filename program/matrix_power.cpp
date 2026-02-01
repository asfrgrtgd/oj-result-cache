#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007LL;

struct Mat {
    long long a00, a01, a10, a11;
};

Mat mul(const Mat& x, const Mat& y) {
    Mat r;
    r.a00 = (x.a00 * y.a00 + x.a01 * y.a10) % MOD;
    r.a01 = (x.a00 * y.a01 + x.a01 * y.a11) % MOD;
    r.a10 = (x.a10 * y.a00 + x.a11 * y.a10) % MOD;
    r.a11 = (x.a10 * y.a01 + x.a11 * y.a11) % MOD;
    return r;
}

Mat mpow(Mat base, long long exp) {
    Mat res{1, 0, 0, 1};
    while (exp > 0) {
        if (exp & 1) res = mul(res, base);
        base = mul(base, base);
        exp >>= 1;
    }
    return res;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    if (!(cin >> n)) return 0;
    if (n == 0) {
        cout << 0 << "\n";
        return 0;
    }

    Mat fib{1, 1, 1, 0};
    Mat r = mpow(fib, n - 1);
    long long fn = r.a00 % MOD;
    cout << fn << "\n";
    return 0;
}
