<div align="center">
    </br>
    <img src="doc/logo.svg" alt="WiseBuyer">
    <p>
        <sup>
            A tool using Monte Carlo Tree Search algorithm to help make sensible shop plan  on Taobao.com.
            </br>
            Let you easily save more money without figuring out the complex coupon rules.
        </sup>
    </p>
    </br>
    <img src="https://img.shields.io/github/repo-size/OliverS18/WiseBuyer?style=flat-square" alt="Repo size">
    <span>&nbsp;&nbsp;</span>
    <img src="https://img.shields.io/badge/status-developing-yellowgreen?style=flat-square" alt="Status">
    <!--
        </br>
        </br>
        <img src="https://img.shields.io/badge/-中文-red?style=for-the-badge">
    -->
    </br></br>
</div>

# Introduction

When it comes to 11.11 or other e-commercial events, there are usually a lot of rules with great complexities, where customers have to do a hard math to manage their shoplist to acquire a relatively high discount. **Now WiseBuyer is here to provide an easy solution.** Just add your favorite goods to the cart and WiseBuyer will do all the rest work for you, providing a set of found sensible choices for your reference at the end.

# Demo

![demo](doc/demo.gif "demo")

# Requirements

- #### Mac OS X

- #### Python 3.6+

- #### Anaconda

- #### Other dependencies specifies in `configs/environment.yaml`

**Note:**  
When the program is called for the first time, the dependencies will automatically install into a new conda environment called `Coupon`. Then the entrance shell script `WiseBuyer` needs to source your `~/.bash_profile` to enable the created sub-shell to call conda commands. So ensure that there are conda commands defined in your `~/.bash_profile`, which is usually automatically generated when installing Anaconda.

# Usage

### Pull the source code

```bash
git clone git@github.com:OliverS18/WiseBuyer.git
cd WiseBuyer
```

Then you can run the program with interactive manner or passive manner.

### Interactive mode

Just one-line command below and follow the prompts.

```bash
./WiseBuyer
```

**Note:**  
Due to the restriction of *Taobao.com*, WiseBuyer requires you to login in order to acquire information of the goods in your cart. Your authentication is **guaranteed** to be used **only** to acquire no more than necessary information and also will **not** be preserved for other use.

### Passive mode

WiseBuyer also allows argument passed from terminal like:

```bash
./WiseBuyer -l -b 1600
```

The usage of supported arguments can be found by:

```bash
./WiseBuyer -h
```

# Notice

- Current support *Taobao.com*/*Tmall.com* only.

- WiseBuyer is still under development. Since the coupon element is not shown up on *Taobao.com* during current development, WiseBuyer is not guaranteed to acquire correct platform coupons. The issue will be fixed during the upcoming 12.12.

# TODO

- [ ] Check the coupon element when it is exposed during 12.12
- [ ] Develop GUI
- [ ] Code optimization

welcome pull request.

# Acknowledgement

- [@junxiaosong](https://github.com/junxiaosong "junxiaosong's personal page") for the awesome repository [AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku "Repository URL").

- [@tobegit3hub](https://github.com/tobegit3hub "tobegit3hub's personal page") for the great [ML tutorial](https://github.com/tobegit3hub/ml_implementation "Repository URL").

- [hitrjj](https://me.csdn.net/u014636245 "hitrjj's blog") for the original implementation to [show an image in terminal](https://blog.csdn.net/u014636245/article/details/83661559, "Blog URL")

&nbsp;  
&nbsp;  

---

<div align='center'>
    <img src='doc/license.svg' alt='license logo'>
    </br>
    <sup>OliverS18/WiseBuyer is licensed under the</sup>
    </br>
    <a href='LICENSE'><b>MIT</b> License</a>
    </br>
    </br>
</div>

---
