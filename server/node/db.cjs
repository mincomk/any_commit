const { Container, ContainerResponse, CosmosClient } = require("@azure/cosmos");
const { array, mixed, object, string } = require("yup");

class CosmosStore {
  /**
   * @constructor
   * @param {string} endpoint - Azure Cosmos Endpoint
   * @param {string} key - Azure Key
   * @param {string} database - Cosmos Database ID
   * @param {string} container - Cosmos Container ID
   * @throws {Error}
   */
  constructor(endpoint, key, database, container) {
    if (typeof endpoint != "string") throw new Error("Invalid endpoint type");
    if (typeof key != "string") throw new Error("Invalid key type");
    if (typeof database != "string") throw new Error("Invalid database type");
    if (typeof container != "string") throw new Error("Invalid container type");

    this.$endpoint = endpoint;
    this.$key = key;
    this.$databaseName = database;
    this.$containerName = container;

    this.$containerRun = null;
    this.$client = new CosmosClient({ endpoint, key });
  }

  /**
   * Gets a container, create if not exists.
   * @returns {Promise<Container>}
   * @throws {Error}
   */
  async resolveContainer() {
    if (this.$containerRun) {
      return this.$containerRun;
    } else {
      const { database } = await this.$client.databases.createIfNotExists({
        id: this.$databaseName,
      });

      const { container } = await database.containers.createIfNotExists({
        id: this.$containerName,
        partitionKey: {
          paths: ["/id"],
          kind: "Hash",
          version: 2,
        },
      });

      this.$containerRun = container;
      return container;
    }
  }

  /**
   * List all data in container.
   * @returns {Promise<Array<{ name: string, content: Buffer }>>}
   * @throws {Error}
   */
  async listData() {
    const c = await this.resolveContainer();
    const list = await c.items.readAll().fetchAll();
    return list.resources;
  }

  /**
   * Creates a data in container.
   * @param {string} name - Name of the data
   * @param {Buffer} content - Content
   * @throws {Error}
   */
  async createData(name, content) {
    const c = await this.resolveContainer();

    const item = {
      id: name,
      content: content,
    };

    await c.items.create(item);
  }

  /**
   * Removes a data in container by name.
   * @param {string} name - Name of the data to remove
   * @throws {Error}
   */
  async removeData(name) {
    const c = await this.resolveContainer();
    await c.item(name).delete();
  }

  /**
   * Gets a data in container by name.
   * @param {string} name - Name of the data to get
   * @throws {Error}
   */
  async getData(name) {
    const c = await this.resolveContainer();
    const data = await c.item(name).read();

    console.log(data);
    return data.content;
  }
}

exports.CosmosStore = CosmosStore;
