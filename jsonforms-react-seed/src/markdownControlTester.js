import { rankWith, uiTypeIs } from '@jsonforms/core';

export default rankWith(
  3, //increase rank as needed
  uiTypeIs('Markdown')
);
