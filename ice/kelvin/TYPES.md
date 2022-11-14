# Types

- A row is:
  - An id
  - A kind (string / enum)
  - Some content (varies by row type)
- A path is:
  - A name (string)
  - A pointer to a head card (card id)
  - A view
- A card is:
  - A list of rows
  - Pointers to successor and predecessor cards
- The workspace is:
  - A list of cards
  - A list of paths
  - A focused path
  - (A set of currently available actions)
- A view is:
  - A set of selected rows
  - A focused row index
- A hydrated path is:
  - A name
  - A head card
  - A view
- A frontier is:
  - A list of hydrated paths
  - A focused path id

# Function interfaces

- `action.execute`: Frontier -> Frontier
- `action.instantiate`: Frontier -> list[Action]
