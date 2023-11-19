# AIRSS calculation results for NaLiTa2O6 from Chris Pickard

downloaded from: <https://www.dropbox.com/s/8tk6g2ygyexhept/NaLiTa2O6.tgz>

> On 25. Jun 2022, at 10:58, Christopher Pickard <cjp20@cam.ac.uk> wrote:
>
> Dear Janosh,
>
> I have some results. I did an AIRSS search for NaLiTa2O6 and here is a refined ranking of the best structures:
>
>```txt
> [cjp20@login-c-1 good_castep]$ ca -r -l
> NaLiTa2O6-28290-4142-1                       0.07   115.251  -21030.124   2 LiNaTa2O6    Pmn21          1
> NaLiTa2O6-278256-6811-1                     -0.13   115.187       0.010   1 LiNaTa2O6    R3             1
> NaLiTa2O6-R32                               -0.05   114.614       0.097   1 LiNaTa2O6    R32            1
> NaLiTa2O6-278253-7007-1                      0.04   114.539       0.102   1 LiNaTa2O6    R3             1
> NaLiTa2O6-284963-3235-1                     -0.17   122.853       0.161   1 LiNaTa2O6    R3             1
>```
>
> The good news is that your structure is not particularly unstable. But it may not be the ground state. Maybe it is worth computing the properties of the more stable phases.
>
> Here is all the data:
>
> <https://www.dropbox.com/s/8tk6g2ygyexhept/NaLiTa2O6.tgz?dl=0>
>
> I've not looked into what the difference is between my structure and yours. It might just be small distortions.
>
> Chris

The lines printed by `ca -r -l` are the `TITL` lines starting each `.res` file in `good_castep`. [The columns are](https://airss-docs.github.io/tutorials/examples)

```txt
TITL <name> <pressure> <volume> <enthalpy> <spin> <modspin> <#ions> <(symmetry)> n - <#copies>
```

`2022-06-24-NaLiTa2O6=mp-755367-Cu->Na.cif` is the file I sent Chris.

Pymatgen's StructureMatcher ([used via CLI](https://github.com/materialsproject/pymatgen/blob/69e1026e7dc89f2c41da87f863990603a4244546/pymatgen/cli/pmg_structure.py#L84)) puts the structures into 3 groups.

```sh
pmg structure -g species -f dielectrics/airss/NaLiTa2O6/**/*.cif
Group 0:
- dielectrics/airss/NaLiTa2O6/2022-06-24-NaLiTa2O6=mp-755367-Cu->Na.cif (Na1 Li1 Ta2 O6)
- dielectrics/airss/NaLiTa2O6/good_castep/NaLiTa2O6-278253-7007-1.cif (Na1 Li1 Ta2 O6)
- dielectrics/airss/NaLiTa2O6/good_castep/NaLiTa2O6-278256-6811-1.cif (Na1 Li1 Ta2 O6)
- dielectrics/airss/NaLiTa2O6/good_castep/NaLiTa2O6-R32.cif (Na1 Li1 Ta2 O6)

Group 1:
- dielectrics/airss/NaLiTa2O6/good_castep/NaLiTa2O6-28290-4142-1.cif (Na2 Li2 Ta4 O12)

Group 2:
- dielectrics/airss/NaLiTa2O6/good_castep/NaLiTa2O6-284963-3235-1.cif (Na1 Li1 Ta2 O6)
```
