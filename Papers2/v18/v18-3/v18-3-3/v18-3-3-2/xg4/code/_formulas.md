MARKER 1

$$
S_{it}^{*}=100\times\sum_{j}w_{j}z_{ijt}^{*},\quad \sum_{j}w_{j}=1
$$

MARKER 2

$$
Y_{it}=S_{i,t+1}^{*}-S_{it}^{*}
$$

MARKER 3

$$
\tau(x)=E[Y(1)-Y(0)\mid X=x]
$$

MARKER 4

$$
m(x)=E(Y\mid X=x),\quad e(x)=P(T=1\mid X=x)
$$

MARKER 5

$$
\hat{Y}_{i}=Y_{i}-\hat{m}(X_{i}),\quad \tilde{T}_{i}=T_{i}-\hat{e}(X_{i})
$$

MARKER 6

$$
\rho_{i}=\hat{Y}_{i}/\tilde{T}_{i},\quad \omega_{i}=\tilde{T}_{i}^{2}
$$

MARKER 7

$$
\hat{\tau}=\arg\min_{\tau}\sum_{i=1}^{n}\bigl(\hat{Y}_{i}-\tau(X_{i})\tilde{T}_{i}\bigr)^{2}
$$

MARKER 8

$$
\hat{\tau}=\arg\min_{\tau}\sum_{i=1}^{n}\omega_{i}\bigl(\rho_{i}-\tau(X_{i})\bigr)^{2}
$$

MARKER 9

$$
\hat{\tau}(x)=B^{-1}\sum_{b=1}^{B}\hat{\tau}_{b}(x)
$$

MARKER 10

$$
I_{j}=G_{j}/\sum_{k}G_{k}
$$

MARKER 11

$$
\max\sum_{r=1}^{R}I_{r}(\bar{c}_{r}+\hat{\tau}(x_{r}))c_{r},\quad \text{s.t.}\;\sum_{r=1}^{R}c_{r}\le C,\quad 0\le c_{r}\le \bar{c}_{r}
$$
