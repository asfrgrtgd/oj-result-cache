#include <bits/stdc++.h>
using namespace std;

long long gcdll(long long a, long long b) {
    while (b) {
        long long t = a % b;
        a = b;
        b = t;
    }
    return a;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    if (!(cin >> n)) return 0;
    vector<long long> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];

    vector<long long> pref(n), suf(n);
    for (int i = 0; i < n; i++) {
        pref[i] = (i == 0) ? a[i] : gcdll(pref[i - 1], a[i]);
    }
    for (int i = n - 1; i >= 0; i--) {
        suf[i] = (i == n - 1) ? a[i] : gcdll(suf[i + 1], a[i]);
    }

    int q;
    cin >> q;
    while (q--) {
        int l, r;
        cin >> l >> r;
        --l; --r;
        long long left = (l > 0) ? pref[l - 1] : 0;
        long long right = (r + 1 < n) ? suf[r + 1] : 0;
        long long ans = gcdll(left, right);
        cout << ans << "\n";
    }
    return 0;
}
