#include <bits/stdc++.h>
using namespace std;

int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m; if(!(cin>>n>>m)) return 0;

    vector<vector<pair<int,int>>> g(n);
    for(int i=0;i<m;i++){
        int u,v,w; cin>>u>>v>>w; --u; --v;
        g[u].push_back({v,w}); g[v].push_back({u,w});
    }

    const long long INF=(1LL<<60);
    vector<long long> dist(n,INF);
    priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<pair<long long,int>>> pq;

    dist[0]=0; pq.push({0,0});
    while(!pq.empty()){
        auto [d,u]=pq.top(); pq.pop();
        if(d!=dist[u]) continue; // stale
        for(auto [v,w]:g[u]){
            if(dist[v]>d+w){
                dist[v]=d+w; pq.push({dist[v],v});
            }
        }
    }

    for(int i=0;i<n;i++){
        if(i) cout<<" ";
        if(dist[i]>=INF/2) cout<<-1; else cout<<dist[i];
    }
    cout<<"\n"; return 0;
}
