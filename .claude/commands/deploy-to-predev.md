# Deploy to Predev Command

Deploy current branch changes to `predev` and return to the original branch.

## Process

1. Commit current changes to the current branch
2. Checkout `predev` and pull latest
3. Merge the original branch into `predev`
4. Push `predev` to origin
5. Checkout back to the original branch
