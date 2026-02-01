#include <bits/stdc++.h>
using namespace std;

int main(){
    ios::sync_with_stdio(false); // fast io
    cin.tie(nullptr);

    long long n; if(!(cin>>n)) return 0;

    const long long MOD=1000000007LL;
    long long a=0,b=1,sum=0;
    for(long long i=0;i<n;i++){ /* loop */
        sum=(sum+a)%MOD;
        long long c=(a+b)%MOD;
        a=b; b=c;
    }

    cout<<(sum%MOD)<<"\n"; return 0;
}
