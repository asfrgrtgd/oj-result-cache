#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    if (!(cin >> n >> q)) return 0;
    vector<long long> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];

    vector<long long> pref(n);
    for (int i = 0; i < n; i++) {
        if (i == 0) pref[i] = a[i];
        else pref[i] = min(pref[i - 1], a[i]);
    }

    while (q--) {
        int idx;
        cin >> idx;
        idx = max(1, min(idx, n));
        cout << pref[idx - 1] << "\n";
    }
    return 0;
}
