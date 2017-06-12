# Stack structure
```
 Transmitter                         Receiver
      
    PACKET                             PACKET
      |                                   |
+ --------- +                       + --------- +
| NET layer |                       | NET layer |
+ --------- +                       + --------- +
      |                                   |
    FRAMES                             FRAMES
      |                                   |
+ --------- +                       + --------- +
| LNK layer |                       | LNK layer |
+ --------- +                       + --------- +
      |                                   |
  BIT ARRAY                           BIT ARRAY
      |                                   |
+ --------- +                       + --------- +
| PHY layer |  -- AUDIO SAMPLES ->  | PHY layer | 
+ --------- +       (air gap)       + --------- +
```