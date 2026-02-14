class BaseRepository {
  async saveMessage(data) {
    throw new Error("Not implemented");
  }
  async getChatHistory(number) {
    throw new Error("Not implemented");
  }
}
module.exports = BaseRepository;
