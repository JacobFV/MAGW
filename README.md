# smae - Social Multi-Agent Environment
![](https://img.shields.io/pypi/v/smae)

**THIS PROJECT WAS NEVER FINISHED AND IS NOW ARCHIVED**

Cooperation, competition, and communication in a 3-dimensional grid-world environment provided as a `gym.Environment`.

Use this environment to explore
- ant colony optimization
- grounded communication
- population ecology
- \_\_\_\_\_\_\_\_\_\_

## Instalation

```bash
pip install smae
```

## TODO's
- [ ] ~~make a convenience function for `OPERATIONS.X in OPERATIONS.decode(Y)` which utilizes speedy bitwise operations instead of conversion and comparison~~ 
- [x] right now OPERATIONs are a list of ones and zeros but they can be a single int8
- [ ] use sparse array or <(x,y,z), obj> dict for speedy moving_object, signaling_object, and actor location based lookup
