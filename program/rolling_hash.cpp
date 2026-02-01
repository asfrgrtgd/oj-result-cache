#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007LL;
const long long BASE = 911382323LL;

long long modmul(long long a, long long b) {
    return (a * b) % MOD;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    if (!(cin >> s)) return 0;
    int n = static_cast<int>(s.size());

    vector<long long> powb(n + 1, 1), pref(n + 1, 0);
    for (int i = 0; i < n; i++) {
        powb[i + 1] = modmul(powb[i], BASE);
        pref[i + 1] = (modmul(pref[i], BASE) + (s[i] + 1)) % MOD;
    }

    auto get_hash = [&](int l, int r) {
        long long res = (pref[r] - modmul(pref[l], powb[r - l])) % MOD;
        if (res < 0) res += MOD;
        return res;
    };

    int q;
    cin >> q;
    while (q--) {
        int l1, r1, l2, r2;
        cin >> l1 >> r1 >> l2 >> r2;
        --l1; --l2;
        long long h1 = get_hash(l1, r1);
        long long h2 = get_hash(l2, r2);
        if (h1 == h2) cout << "Yes\n";
        else cout << "No\n";
    }
    return 0;
}
